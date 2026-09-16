from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.match import Match, MatchStatus
from app.services.matching_service import MatchScore


async def create_application_on_match(
    db: AsyncSession,
    candidate_id: uuid.UUID,
    job_listing_id: uuid.UUID,
    score: MatchScore,
) -> tuple[Match, Application]:
    """Create a Match (status='applied') and an Application in a single transaction.

    Called immediately on a candidate's right-swipe when score >= threshold.
    No company action is needed to gate this — the application is submitted
    the moment this function runs.
    """
    from datetime import datetime, timezone

    match = Match(
        candidate_id=candidate_id,
        job_listing_id=job_listing_id,
        score=score.total,
        score_breakdown=score.breakdown,
        matched_at=datetime.now(timezone.utc),
        status=MatchStatus.applied,  # Always 'applied' — no pending state
    )
    db.add(match)
    await db.flush()  # get match.id before creating the application

    application = Application(
        match_id=match.id,
        candidate_id=candidate_id,
        job_listing_id=job_listing_id,
        # status defaults to 'submitted' — company updates this post-hoc
    )
    db.add(application)
    # Caller commits the transaction (swipe + match + application atomically)
    await db.flush()
    return match, application
