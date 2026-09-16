from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_recruiter
from app.core.exceptions import NotFoundError, TenantMismatchError
from app.db.session import get_session
from app.models.job_listing import JobListing
from app.schemas import JobListingCreate, JobListingResponse, JobListingUpdate
from app.services.embedding_service import encode

router = APIRouter(prefix="/company/jobs", tags=["company"])


def _get_tenant_id(payload: dict) -> uuid.UUID:
    tid = payload.get("tenant_id")
    if not tid:
        raise TenantMismatchError("No tenant_id in token.")
    return uuid.UUID(str(tid))


@router.post("", response_model=JobListingResponse, status_code=201)
async def create_job(
    body: JobListingCreate,
    payload: Annotated[dict, Depends(get_current_recruiter)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> JobListingResponse:
    tenant_id = _get_tenant_id(payload)

    # Determine company_id from recruiter's company
    from app.models.company import Recruiter
    recruiter = await db.get(Recruiter, uuid.UUID(payload["sub"]))
    if not recruiter:
        raise NotFoundError("Recruiter not found.")

    listing = JobListing(
        company_id=recruiter.company_id,
        tenant_id=tenant_id,
        **body.model_dump(),
    )

    db.add(listing)
    await db.commit()
    await db.refresh(listing)

    # Generate embedding
    text = f"{body.title} {body.description or ''} {' '.join(body.required_skills or [])}"
    from app.workers.tasks import update_job_embedding
    update_job_embedding.delay(str(listing.id), text.strip())

    return JobListingResponse.model_validate(listing)


@router.get("", response_model=list[JobListingResponse])
async def list_jobs(
    payload: Annotated[dict, Depends(get_current_recruiter)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[JobListingResponse]:
    from app.models.company import Recruiter
    recruiter = await db.get(Recruiter, uuid.UUID(payload["sub"]))
    if not recruiter:
        raise NotFoundError("Recruiter not found.")

    result = await db.execute(
        select(JobListing).where(JobListing.company_id == recruiter.company_id)
    )
    return [JobListingResponse.model_validate(j) for j in result.scalars().all()]


@router.patch("/{job_id}", response_model=JobListingResponse)
async def update_job(
    job_id: uuid.UUID,
    body: JobListingUpdate,
    payload: Annotated[dict, Depends(get_current_recruiter)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> JobListingResponse:
    from app.models.company import Recruiter
    recruiter = await db.get(Recruiter, uuid.UUID(payload["sub"]))
    if not recruiter:
        raise NotFoundError("Recruiter not found.")

    job = await db.get(JobListing, job_id)
    if not job or job.company_id != recruiter.company_id:
        raise NotFoundError("Job listing not found.")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(job, field, value)

    await db.commit()
    await db.refresh(job)

    # Recompute embedding if content changed
    if body.title or body.description or body.required_skills:
        text = f"{job.title} {job.description or ''} {' '.join(job.required_skills or [])}"
        from app.workers.tasks import update_job_embedding
        update_job_embedding.delay(str(job.id), text.strip())

    return JobListingResponse.model_validate(job)
