from __future__ import annotations

import asyncio
import logging
import uuid

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def update_candidate_embedding(self, candidate_id: str, text: str) -> dict:
    """Generate the semantic embedding for a candidate in the background."""
    try:
        return asyncio.run(_update_candidate_embedding(candidate_id, text))
    except Exception as exc:
        logger.exception("update_candidate_embedding failed for %s: %s", candidate_id, exc)
        raise self.retry(exc=exc)


async def _update_candidate_embedding(candidate_id_str: str, text: str) -> dict:
    from app.db.session import AsyncSessionLocal
    from app.models.user import Candidate
    from app.services.embedding_service import encode
    import uuid

    candidate_id = uuid.UUID(candidate_id_str)
    
    # Run the heavy encode operation in a thread to not block this async worker loop
    try:
        embedding = await asyncio.to_thread(encode, text)
    except (TimeoutError, RuntimeError) as e:
        logger.error(
            "embedding_encode_failed candidate_id=%s error=%s",
            candidate_id_str, str(e)
        )
        return {"status": "failed", "reason": "encode_error", "error": str(e)}

    async with AsyncSessionLocal() as db:
        candidate = await db.get(Candidate, candidate_id)
        if candidate:
            candidate.profile_embedding = embedding
            await db.commit()
    
    # Once embedding is saved, trigger recompute
    recompute_matches_for_candidate.delay(candidate_id_str)
    return {"status": "success"}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def update_job_embedding(self, job_listing_id: str, text: str) -> dict:
    """Generate the semantic embedding for a job listing in the background."""
    try:
        return asyncio.run(_update_job_embedding(job_listing_id, text))
    except Exception as exc:
        logger.exception("update_job_embedding failed for %s: %s", job_listing_id, exc)
        raise self.retry(exc=exc)


async def _update_job_embedding(job_listing_id_str: str, text: str) -> dict:
    from app.db.session import AsyncSessionLocal
    from app.models.job_listing import JobListing
    from app.services.embedding_service import encode
    import uuid

    job_id = uuid.UUID(job_listing_id_str)
    
    try:
        embedding = await asyncio.to_thread(encode, text)
    except (TimeoutError, RuntimeError) as e:
        logger.error(
            "embedding_encode_failed job_id=%s error=%s",
            job_listing_id_str, str(e)
        )
        return {"status": "failed", "reason": "encode_error", "error": str(e)}

    async with AsyncSessionLocal() as db:
        job = await db.get(JobListing, job_id)
        if job:
            job.listing_embedding = embedding
            await db.commit()
    
    recompute_matches_for_job.delay(job_listing_id_str)
    return {"status": "success"}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def recompute_matches_for_candidate(self, candidate_id: str) -> dict:
    """Recompute match scores for all active job listings for a given candidate.

    - Called after a candidate edits their profile / skills.
    - Skips listings already swiped left by the candidate (no zombie resurrections).
    - Does NOT create new matches — only updates existing pending ones.
    - Uses asyncio.run to bridge sync Celery task into async SQLAlchemy.
    """
    try:
        return asyncio.run(_recompute_candidate(candidate_id))
    except Exception as exc:
        logger.exception("recompute_matches_for_candidate failed for %s: %s", candidate_id, exc)
        raise self.retry(exc=exc)


async def _recompute_candidate(candidate_id_str: str) -> dict:
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.models.user import Candidate
    from app.models.job_listing import JobListing
    from app.models.swipe import Swipe, SwipeDirection
    from app.models.match import Match
    from app.services.matching_service import compute_match_score, is_match, passes_hard_filters

    candidate_id = uuid.UUID(candidate_id_str)
    updated = 0

    async with AsyncSessionLocal() as db:
        candidate = await db.get(Candidate, candidate_id)
        if not candidate:
            return {"updated": 0, "reason": "candidate_not_found"}

        # Listings swiped LEFT by candidate — never resurface
        left_swiped_subq = (
            select(Swipe.job_listing_id)
            .where(
                Swipe.candidate_id == candidate_id,
                Swipe.direction == SwipeDirection.left,
            )
            .scalar_subquery()
        )

        result = await db.execute(
            select(JobListing)
            .where(JobListing.is_active.is_(True))
            .where(JobListing.id.not_in(left_swiped_subq))
        )
        jobs = result.scalars().all()

        for job in jobs:
            if not passes_hard_filters(candidate, job):
                continue
            score = compute_match_score(candidate, job)

            # Update existing match if present
            existing_match = await db.scalar(
                select(Match).where(
                    Match.candidate_id == candidate_id,
                    Match.job_listing_id == job.id,
                )
            )
            if existing_match:
                existing_match.score = score.total
                existing_match.score_breakdown = score.breakdown
                updated += 1

        await db.commit()

    return {"updated": updated}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def recompute_matches_for_job(self, job_listing_id: str) -> dict:
    """Recompute scores for all candidates with a pending match on this listing.

    Called after a job listing is edited.
    """
    try:
        return asyncio.run(_recompute_job(job_listing_id))
    except Exception as exc:
        logger.exception("recompute_matches_for_job failed for %s: %s", job_listing_id, exc)
        raise self.retry(exc=exc)


async def _recompute_job(job_listing_id_str: str) -> dict:
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.models.job_listing import JobListing
    from app.models.match import Match
    from app.models.user import Candidate
    from app.services.matching_service import compute_match_score, passes_hard_filters

    job_id = uuid.UUID(job_listing_id_str)
    updated = 0

    async with AsyncSessionLocal() as db:
        job = await db.get(JobListing, job_id)
        if not job or not job.is_active:
            return {"updated": 0}

        result = await db.execute(select(Match).where(Match.job_listing_id == job_id))
        matches = result.scalars().all()

        for match in matches:
            candidate = await db.get(Candidate, match.candidate_id)
            if candidate and passes_hard_filters(candidate, job):
                score = compute_match_score(candidate, job)
                match.score = score.total
                match.score_breakdown = score.breakdown
                updated += 1

        await db.commit()

    return {"updated": updated}
