from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_recruiter
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.db.session import get_session
from app.models.application import Application, ApplicationStatus
from app.models.company import Recruiter
from app.models.job_listing import JobListing
from app.schemas import ApplicationResponse, ApplicationStatusUpdate

router = APIRouter(tags=["company"])

# Only these transitions are allowed from the recruiter dashboard
_ALLOWED_COMPANY_STATUSES = {ApplicationStatus.rejected, ApplicationStatus.interview}


@router.get("/company/jobs/{job_id}/applications", response_model=list[ApplicationResponse])
async def list_applications(
    job_id: uuid.UUID,
    payload: Annotated[dict, Depends(get_current_recruiter)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[ApplicationResponse]:
    """All auto-matched applications for this listing, scoped to the recruiter's company.

    Applications arrive here automatically when a candidate's right-swipe scores
    >= threshold — no recruiter action was needed to populate this list.
    """
    recruiter = await db.get(Recruiter, uuid.UUID(payload["sub"]))
    if not recruiter:
        raise NotFoundError("Recruiter not found.")

    job = await db.get(JobListing, job_id)
    if not job or job.company_id != recruiter.company_id:
        raise NotFoundError("Job listing not found.")

    result = await db.execute(
        select(Application).where(Application.job_listing_id == job_id)
    )
    return [ApplicationResponse.model_validate(a) for a in result.scalars().all()]


@router.patch("/company/applications/{application_id}", response_model=ApplicationResponse)
async def update_application_status(
    application_id: uuid.UUID,
    body: ApplicationStatusUpdate,
    payload: Annotated[dict, Depends(get_current_recruiter)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ApplicationResponse:
    """Recruiter moves an application to 'rejected' or 'interview'.

    Only these two transitions are valid — 'submitted' / 'viewed' cannot be
    set by the company directly. This is a status update, never a deletion;
    rejection does not retract the application or remove it from the candidate's view.
    """
    recruiter = await db.get(Recruiter, uuid.UUID(payload["sub"]))
    if not recruiter:
        raise NotFoundError("Recruiter not found.")

    application = await db.get(Application, application_id)
    if not application:
        raise NotFoundError("Application not found.")

    # Ensure the application belongs to this recruiter's company
    job = await db.get(JobListing, application.job_listing_id)
    if not job or job.company_id != recruiter.company_id:
        raise ForbiddenError("You do not have access to this application.")

    new_status = ApplicationStatus(body.status)
    if new_status not in _ALLOWED_COMPANY_STATUSES:
        raise ValidationAppError(
            f"Invalid status transition. Allowed values: "
            f"{', '.join(s.value for s in _ALLOWED_COMPANY_STATUSES)}",
            field="status",
        )

    application.status = new_status
    await db.commit()
    await db.refresh(application)
    return ApplicationResponse.model_validate(application)
