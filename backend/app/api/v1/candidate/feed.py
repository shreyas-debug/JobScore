from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_candidate
from app.core.exceptions import NotFoundError
from app.db.session import get_session
from app.models.user import Candidate
from app.models.job_listing import JobListing
from app.models.company import Company
from app.models.swipe import Swipe
from app.schemas import FeedResponse, JobCardResponse

router = APIRouter(prefix="/candidate/feed", tags=["candidate"])

DEFAULT_PAGE_SIZE = 20


@router.get("", response_model=FeedResponse)
async def get_feed(
    payload: Annotated[dict, Depends(get_current_candidate)],
    db: Annotated[AsyncSession, Depends(get_session)],
    cursor: str | None = None,
    limit: int = DEFAULT_PAGE_SIZE,
) -> FeedResponse:
    """Return ranked, unswiped active job listings for this candidate."""
    import base64
    from app.services.matching_service import compute_match_score, passes_hard_filters

    candidate_id = uuid.UUID(payload["sub"])
    candidate = await db.get(Candidate, candidate_id)
    if not candidate:
        raise NotFoundError("Candidate not found.")

    # Pull unswiped active listings, eager-loading company so we get the name
    stmt = (
        select(JobListing)
        .options(selectinload(JobListing.company))
        .where(JobListing.is_active.is_(True))
        .where(~JobListing.id.in_(
            select(Swipe.job_listing_id)
            .where(Swipe.candidate_id == candidate_id)
        ))
        .limit(500)
    )

    result = await db.execute(stmt)
    listings = result.scalars().all()

    # Hard filter — be lenient for users with no profile yet
    has_profile = bool(candidate.skills or candidate.resume_summary)
    if has_profile:
        survivors = [j for j in listings if passes_hard_filters(candidate, j)]
    else:
        survivors = list(listings)

    # Score & rank
    scored = [(j, compute_match_score(candidate, j).total) for j in survivors]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Paginate
    offset = 0
    if cursor:
        try:
            offset = int(base64.b64decode(cursor.encode()).decode())
        except Exception:
            offset = 0

    page = scored[offset: offset + limit]
    has_more = (offset + limit) < len(scored)
    next_cursor = base64.b64encode(str(offset + limit).encode()).decode() if has_more else None

    items = []
    for job, _ in page:
        card = JobCardResponse.model_validate(job)
        # Inject company name from the eager-loaded relationship
        if job.company:
            card.company_name = job.company.name
            card.company_industry = job.company.industry
        items.append(card)

    return FeedResponse(items=items, next_cursor=next_cursor)
