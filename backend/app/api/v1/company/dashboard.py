from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_recruiter
from app.core.exceptions import NotFoundError
from app.db.session import get_session
from app.models.application import Application, ApplicationStatus
from app.models.company import Recruiter
from app.models.job_listing import JobListing
from app.models.match import Match
from app.schemas import DashboardResponse

router = APIRouter(prefix="/company/dashboard", tags=["company"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    payload: Annotated[dict, Depends(get_current_recruiter)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> DashboardResponse:
    """Funnel: auto-matched applications → interview-stage → rejected.

    All counts are scoped to the requesting tenant via explicit company_id filter
    (RLS provides a second layer of protection).
    """
    recruiter = await db.get(Recruiter, uuid.UUID(payload["sub"]))
    if not recruiter:
        raise NotFoundError("Recruiter not found.")

    company_id = recruiter.company_id

    job_ids_result = await db.execute(
        select(JobListing.id).where(JobListing.company_id == company_id)
    )
    job_ids = [row[0] for row in job_ids_result]

    if not job_ids:
        return DashboardResponse(
            total_matches=0,
            total_swiped=0,
            total_applied=0,
            avg_score=None,
            funnel={"submitted": 0, "interview": 0, "rejected": 0},
        )

    # Total auto-matched applications landing in the dashboard
    total_applied = await db.scalar(
        select(func.count(Application.id)).where(Application.job_listing_id.in_(job_ids))
    ) or 0

    # Interview-stage count
    interview_count = await db.scalar(
        select(func.count(Application.id)).where(
            Application.job_listing_id.in_(job_ids),
            Application.status == ApplicationStatus.interview,
        )
    ) or 0

    # Rejected count
    rejected_count = await db.scalar(
        select(func.count(Application.id)).where(
            Application.job_listing_id.in_(job_ids),
            Application.status == ApplicationStatus.rejected,
        )
    ) or 0

    # Avg match score
    avg_score_row = await db.scalar(
        select(func.avg(Match.score)).where(Match.job_listing_id.in_(job_ids))
    )

    total_matches = await db.scalar(
        select(func.count(Match.id)).where(Match.job_listing_id.in_(job_ids))
    ) or 0

    return DashboardResponse(
        total_matches=total_matches,
        total_swiped=total_applied,   # "swiped" is now "applications received"
        total_applied=total_applied,
        avg_score=float(avg_score_row) if avg_score_row else None,
        funnel={
            "submitted": total_applied,
            "interview": interview_count,
            "rejected": rejected_count,
        },
    )
