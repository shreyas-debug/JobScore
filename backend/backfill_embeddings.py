"""Backfill listing_embedding for any job_listings that are missing one.

Run inside the container:
    docker compose exec backend python backfill_embeddings.py
"""
import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.job_listing import JobListing
from app.services.embedding_service import encode


async def backfill():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(JobListing).where(JobListing.listing_embedding.is_(None))
        )
        jobs = result.scalars().all()

        if not jobs:
            print("All listings already have embeddings.")
            return

        print(f"Backfilling {len(jobs)} listing(s)...")
        for job in jobs:
            skill_names = " ".join(
                s["skill"] if isinstance(s, dict) else s
                for s in (job.required_skills or [])
            )
            text = f"{job.title} {job.description or ''} {skill_names}".strip()
            try:
                job.listing_embedding = encode(text)
                print(f"  OK  {job.title}")
            except Exception as e:
                print(f"  FAIL {job.title}: {e}")

        await session.commit()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(backfill())
