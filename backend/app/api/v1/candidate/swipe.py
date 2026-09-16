from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_candidate
from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, RateLimitError
from app.db.session import get_session
from app.models.job_listing import JobListing
from app.models.match import Match, MatchStatus
from app.models.swipe import Swipe, SwipeDirection
from app.models.user import Candidate
from app.schemas import CandidateSwipeRequest, MatchBreakdownResponse, MatchResponse, SwipeResponse
from app.services.application_service import create_application_on_match
from app.services.matching_service import compute_match_score, is_match, passes_hard_filters

router = APIRouter(prefix="/candidate", tags=["candidate"])


def _seconds_until_midnight_utc() -> int:
    now = datetime.now(timezone.utc)
    from datetime import timedelta
    next_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return int((next_midnight - now).total_seconds())


@router.post("/swipe", response_model=SwipeResponse)
async def candidate_swipe(
    body: CandidateSwipeRequest,
    payload: Annotated[dict, Depends(get_current_candidate)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> SwipeResponse:
    """Candidate swipes on a job listing.

    On a right-swipe:
      1. Hard filters run.
      2. If they pass, soft score is computed immediately (in the same request).
      3. If score >= threshold, a Match + Application are written atomically.
         The application is auto-submitted — no company action is needed to gate it.
      4. If score < threshold, the swipe is recorded but nothing surfaces to the company.

    Company-side action (accept/reject) is a post-hoc status update on an already-
    existing Application, done from the recruiter dashboard.
    """
    candidate_id = uuid.UUID(payload["sub"])

    # ── daily cap check ────────────────────────────────────────────────────
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    swipe_count = await db.scalar(
        select(func.count(Swipe.id)).where(
            Swipe.candidate_id == candidate_id,
            Swipe.created_at >= today_start,
        )
    )
    if (swipe_count or 0) >= settings.DAILY_SWIPE_CAP:
        raise RateLimitError(
            f"Daily swipe cap of {settings.DAILY_SWIPE_CAP} reached. Resets at midnight UTC.",
            retry_after=_seconds_until_midnight_utc(),
        )

    # ── idempotency: return 409 if already swiped ─────────────────────────
    existing = await db.scalar(
        select(Swipe).where(
            Swipe.candidate_id == candidate_id,
            Swipe.job_listing_id == body.job_listing_id,
        )
    )
    if existing:
        raise ConflictError("You have already swiped on this listing.")

    # ── record swipe ───────────────────────────────────────────────────────
    swipe = Swipe(
        candidate_id=candidate_id,
        job_listing_id=body.job_listing_id,
        direction=SwipeDirection(body.direction),
    )
    db.add(swipe)

    matched = False
    match_id = None
    application_id = None
    score_val = None
    score_breakdown = None

    # ── right-swipe: run matching immediately ─────────────────────────────
    if body.direction == "right":
        candidate = await db.get(Candidate, candidate_id)
        job = await db.get(JobListing, body.job_listing_id)

        if not job or not job.is_active:
            raise NotFoundError("Job listing not found or no longer active.")

        if candidate and passes_hard_filters(candidate, job):
            score = compute_match_score(candidate, job)
            if is_match(score.total):
                # Atomically write the Match + Application in the same transaction
                new_match, new_app = await create_application_on_match(db, candidate_id, body.job_listing_id, score)
                matched = True
                match_id = new_match.id
                application_id = new_app.id
                score_val = score.total
                score_breakdown = score.breakdown

    try:
        await db.commit()
        await db.refresh(swipe)
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Duplicate swipe.")

    return SwipeResponse(
        id=swipe.id,
        direction=swipe.direction,
        created_at=swipe.created_at,
        matched=matched,
        match_id=match_id,
        application_id=application_id,
        score=score_val,
        score_breakdown=score_breakdown,
    )


@router.get("/matches", response_model=list[MatchResponse])
async def get_matches(
    payload: Annotated[dict, Depends(get_current_candidate)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[MatchResponse]:
    from sqlalchemy.orm import selectinload
    candidate_id = uuid.UUID(payload["sub"])
    result = await db.execute(
        select(Match)
        .options(selectinload(Match.job_listing).selectinload(JobListing.company))
        .where(Match.candidate_id == candidate_id)
    )
    matches = result.scalars().all()
    
    from app.schemas import JobCardResponse
    items = []
    for m in matches:
        card = None
        if m.job_listing:
            card = JobCardResponse.model_validate(m.job_listing)
            if m.job_listing.company:
                card.company_name = m.job_listing.company.name
                card.company_industry = m.job_listing.company.industry
        
        items.append(
            MatchResponse(
                id=m.id,
                candidate_id=m.candidate_id,
                job_listing_id=m.job_listing_id,
                score=m.score,
                status=m.status.value if hasattr(m.status, "value") else str(m.status),
                matched_at=m.matched_at,
                created_at=m.created_at,
                job_listing=card
            )
        )
    return items


@router.delete("/swipes")
async def reset_swipes(
    payload: Annotated[dict, Depends(get_current_candidate)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """DEV ONLY: Reset candidate's swipes and matches to test the deck again."""
    candidate_id = uuid.UUID(payload["sub"])
    from app.models.application import Application
    from sqlalchemy import delete

    # Delete applications -> matches -> swipes
    await db.execute(delete(Application).where(Application.candidate_id == candidate_id))
    await db.execute(delete(Match).where(Match.candidate_id == candidate_id))
    await db.execute(delete(Swipe).where(Swipe.candidate_id == candidate_id))
    await db.commit()
    return {"status": "reset_successful"}


@router.get("/matches/{match_id}/breakdown", response_model=MatchBreakdownResponse)
async def get_match_breakdown(
    match_id: uuid.UUID,
    payload: Annotated[dict, Depends(get_current_candidate)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> MatchBreakdownResponse:
    candidate_id = uuid.UUID(payload["sub"])
    match = await db.scalar(
        select(Match).where(Match.id == match_id, Match.candidate_id == candidate_id)
    )
    if not match:
        raise NotFoundError("Match not found.")
    return MatchBreakdownResponse(
        id=match.id,
        score=match.score,
        score_breakdown=match.score_breakdown,
        status=match.status,
    )

@router.get("/debug-swipe")
async def debug_swipe(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    import traceback
    try:
        candidate = await db.scalar(select(Candidate).limit(1))
        job = await db.scalar(select(JobListing).where(JobListing.title.ilike("%Senior Full-Stack Engineer%")).limit(1))
        if not candidate or not job:
            return {"error": "Missing seed data"}
        
        score = compute_match_score(candidate, job)
        new_match, new_app = await create_application_on_match(db, candidate.id, job.id, score)
        await db.commit()
        return {"success": True, "match_id": new_match.id, "app_id": new_app.id}
    except Exception as e:
        await db.rollback()
        return {"error": str(e), "traceback": traceback.format_exc()}


