import asyncio
from app.db.session import async_session_maker
from app.models.user import Candidate
from app.models.job_listing import JobListing
from app.models.swipe import Swipe
from sqlalchemy import select
from app.api.v1.candidate.swipe import compute_match_score, create_application_on_match

async def run():
    async with async_session_maker() as db:
        candidate = await db.scalar(select(Candidate).limit(1))
        job = await db.scalar(select(JobListing).limit(1))
        
        if not candidate or not job:
            print("Missing candidate or job")
            return
            
        print(f"Candidate: {candidate.id}")
        print(f"Job: {job.id}")
        
        try:
            swipe = Swipe(
                candidate_id=candidate.id,
                job_listing_id=job.id,
                direction="right"
            )
            db.add(swipe)
            
            score = compute_match_score(candidate, job)
            print(f"Score: {score.total}")
            
            if score.total >= 0.6:
                await create_application_on_match(db, candidate.id, job.id, score)
                print("Created match + application")
            
            await db.commit()
            print("Commit successful")
        except Exception as e:
            print(f"Error during commit: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(run())
