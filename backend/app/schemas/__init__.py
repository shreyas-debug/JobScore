from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Candidate ────────────────────────────────────────────────────────────


class CandidateRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=255)


class CandidateProfileUpdate(BaseModel):
    name: str | None = None
    resume_summary: str | None = None
    skills: list[str] | None = None
    years_experience: int | None = Field(default=None, ge=0)
    desired_salary_min: int | None = Field(default=None, ge=0)
    desired_salary_max: int | None = Field(default=None, ge=0)
    location: str | None = None
    remote_ok: bool | None = None


class CandidateProfileResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    name: str
    resume_summary: str | None
    skills: list[str] | None
    years_experience: int
    desired_salary_min: int | None
    desired_salary_max: int | None
    location: str | None
    remote_ok: bool
    created_at: datetime


# ── Company / Recruiter ───────────────────────────────────────────────────


class CompanyRegisterRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    industry: str | None = None
    description: str | None = None
    recruiter_email: EmailStr
    recruiter_password: str = Field(min_length=8)


class CompanyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    industry: str | None
    description: str | None
    tenant_id: uuid.UUID
    created_at: datetime


# ── Auth ─────────────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Job Listings ──────────────────────────────────────────────────────────


class JobListingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    required_skills: list[str] | None = None
    min_years_experience: int = Field(default=0, ge=0)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    location: str | None = None
    remote_ok: bool = False
    seniority: str | None = None


class JobListingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    required_skills: list[str] | None = None
    min_years_experience: int | None = Field(default=None, ge=0)
    salary_min: int | None = None
    salary_max: int | None = None
    location: str | None = None
    remote_ok: bool | None = None
    seniority: str | None = None
    is_active: bool | None = None


class JobListingResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    title: str
    description: str | None
    required_skills: list[str] | None
    min_years_experience: int
    salary_min: int | None
    salary_max: int | None
    location: str | None
    remote_ok: bool
    seniority: str | None
    is_active: bool
    created_at: datetime


# ── Swipe ─────────────────────────────────────────────────────────────────


class CandidateSwipeRequest(BaseModel):
    job_listing_id: uuid.UUID
    direction: str = Field(pattern="^(left|right)$")


class SwipeResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    direction: str
    created_at: datetime
    matched: bool = False
    match_id: uuid.UUID | None = None
    application_id: uuid.UUID | None = None
    score: float | None = None
    score_breakdown: dict | None = None

# ── Match ─────────────────────────────────────────────────────────────────


class MatchResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    candidate_id: uuid.UUID
    job_listing_id: uuid.UUID
    score: float
    status: str  # 'applied' | 'withdrawn'
    matched_at: datetime | None
    created_at: datetime
    job_listing: "JobCardResponse | None" = None


class MatchBreakdownResponse(BaseModel):
    id: uuid.UUID
    score: float
    score_breakdown: dict | None
    status: str  # 'applied' | 'withdrawn'


class ApplicationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    match_id: uuid.UUID
    candidate_id: uuid.UUID
    job_listing_id: uuid.UUID
    status: str  # 'submitted' | 'viewed' | 'rejected' | 'interview'
    created_at: datetime


class ApplicationStatusUpdate(BaseModel):
    """Only 'rejected' and 'interview' are valid company-side transitions."""
    status: str = Field(pattern="^(rejected|interview)$")


# ── Feed ──────────────────────────────────────────────────────────────────


class JobCardResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    company_id: uuid.UUID
    company_name: str | None = None
    company_industry: str | None = None
    description: str | None
    required_skills: list[str] | None
    salary_min: int | None
    salary_max: int | None
    location: str | None
    remote_ok: bool
    seniority: str | None


class CandidateCardResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    skills: list[str] | None
    years_experience: int
    location: str | None
    remote_ok: bool


class FeedResponse(BaseModel):
    items: list[JobCardResponse]
    next_cursor: str | None


class CandidateFeedResponse(BaseModel):
    items: list[CandidateCardResponse]
    next_cursor: str | None


# ── Dashboard ─────────────────────────────────────────────────────────────


class DashboardResponse(BaseModel):
    total_matches: int
    total_swiped: int
    total_applied: int
    avg_score: float | None
    funnel: dict[str, int]
