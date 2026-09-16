from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    InvalidTokenError,
)
from app.db.session import get_session
from app.models.company import Company, Recruiter
from app.models.user import Candidate
from app.schemas import (
    CandidateRegisterRequest,
    CompanyRegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/candidate/register", response_model=TokenResponse, status_code=201)
async def register_candidate(
    body: CandidateRegisterRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    existing = await db.scalar(select(Candidate).where(Candidate.email == body.email))
    if existing:
        raise ConflictError("Email already registered.")

    hashed_pw = await asyncio.to_thread(hash_password, body.password)
    candidate = Candidate(
        email=body.email,
        hashed_password=hashed_pw,
        name=body.name,
    )
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)

    access = create_access_token(subject=str(candidate.id), role="candidate")
    refresh = create_refresh_token(subject=str(candidate.id))
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/company/register", response_model=TokenResponse, status_code=201)
async def register_company(
    body: CompanyRegisterRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    existing = await db.scalar(select(Recruiter).where(Recruiter.email == body.recruiter_email))
    if existing:
        raise ConflictError("Recruiter email already registered.")

    tenant_id = uuid.uuid4()
    company = Company(name=body.company_name, industry=body.industry, description=body.description, tenant_id=tenant_id)
    db.add(company)
    await db.flush()

    hashed_pw = await asyncio.to_thread(hash_password, body.recruiter_password)
    recruiter = Recruiter(
        company_id=company.id,
        email=body.recruiter_email,
        hashed_password=hashed_pw,
        role="owner",
    )
    db.add(recruiter)
    await db.commit()
    await db.refresh(recruiter)

    access = create_access_token(
        subject=str(recruiter.id), role="owner", tenant_id=str(tenant_id)
    )
    refresh = create_refresh_token(subject=str(recruiter.id))
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_session)) -> TokenResponse:
    # Try candidate first
    candidate = await db.scalar(select(Candidate).where(Candidate.email == body.email))
    if candidate:
        is_valid = await asyncio.to_thread(verify_password, body.password, candidate.hashed_password)
        if is_valid:
            access = create_access_token(subject=str(candidate.id), role="candidate")
            refresh = create_refresh_token(subject=str(candidate.id))
            return TokenResponse(access_token=access, refresh_token=refresh)

    # Try recruiter
    recruiter = await db.scalar(select(Recruiter).where(Recruiter.email == body.email))
    if recruiter:
        is_valid = await asyncio.to_thread(verify_password, body.password, recruiter.hashed_password)
        if is_valid:
            company = await db.get(Company, recruiter.company_id)
            access = create_access_token(
                subject=str(recruiter.id),
                role=recruiter.role,
                tenant_id=str(company.tenant_id) if company else None,
            )
            refresh = create_refresh_token(subject=str(recruiter.id))
            return TokenResponse(access_token=access, refresh_token=refresh)

    raise UnauthorizedError("Invalid email or password.")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    try:
        payload = decode_token(body.refresh_token)
    except InvalidTokenError as exc:
        raise UnauthorizedError("Invalid or expired refresh token.") from exc

    if payload.get("type") != "refresh":
        raise UnauthorizedError("Not a refresh token.")

    subject = payload["sub"]

    # Look up the user to get fresh role/tenant claims
    recruiter = await db.get(Recruiter, uuid.UUID(subject))
    if recruiter:
        company = await db.get(Company, recruiter.company_id)
        access = create_access_token(
            subject=subject,
            role=recruiter.role,
            tenant_id=str(company.tenant_id) if company else None,
        )
    else:
        candidate = await db.get(Candidate, uuid.UUID(subject))
        if candidate:
            access = create_access_token(subject=subject, role="candidate")
        else:
            raise UnauthorizedError("User no longer exists.")

    refresh = create_refresh_token(subject=subject)
    return TokenResponse(access_token=access, refresh_token=refresh)
