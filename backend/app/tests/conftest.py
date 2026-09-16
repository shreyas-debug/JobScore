from __future__ import annotations

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.models.company import Company, Recruiter
from app.models.job_listing import JobListing
from app.models.user import Candidate

# ── In-memory-style test DB ───────────────────────────────────────────────
# Uses a real Postgres (via testcontainers or a docker-compose test DB)
# If POSTGRES is not available in CI, this can be swapped to aiosqlite for unit tests.

TEST_DATABASE_URL = "postgresql+asyncpg://jobscore:jobscore@localhost:5432/jobscore_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client wired to the test DB session."""

    async def override_get_session():
        yield db

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Fixture helpers ───────────────────────────────────────────────────────


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login_as_candidate(candidate: Candidate) -> str:
    return create_access_token(subject=str(candidate.id), role="candidate")


def login_as_recruiter(recruiter: Recruiter, tenant_id: uuid.UUID) -> str:
    return create_access_token(
        subject=str(recruiter.id), role=recruiter.role, tenant_id=str(tenant_id)
    )


@pytest_asyncio.fixture
async def seed_candidate(db: AsyncSession) -> Candidate:
    candidate = Candidate(
        email=f"candidate-{uuid.uuid4().hex[:6]}@test.com",
        hashed_password=hash_password("password123"),
        name="Test Candidate",
        years_experience=3,
        desired_salary_min=80_000,
        desired_salary_max=120_000,
        location="New York",
        remote_ok=False,
        skills=["Python", "FastAPI"],
    )
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    return candidate


@pytest_asyncio.fixture
async def seed_company(db: AsyncSession) -> tuple[Company, Recruiter]:
    tenant_id = uuid.uuid4()
    company = Company(name="Acme Corp", tenant_id=tenant_id)
    db.add(company)
    await db.flush()
    recruiter = Recruiter(
        company_id=company.id,
        email=f"recruiter-{uuid.uuid4().hex[:6]}@test.com",
        hashed_password=hash_password("password123"),
        role="owner",
    )
    db.add(recruiter)
    await db.commit()
    await db.refresh(company)
    await db.refresh(recruiter)
    return company, recruiter


@pytest_asyncio.fixture
async def seed_job(db: AsyncSession, seed_company) -> tuple[JobListing, Company, Recruiter]:
    company, recruiter = seed_company
    job = JobListing(
        company_id=company.id,
        tenant_id=company.tenant_id,
        title="Backend Engineer",
        min_years_experience=2,
        salary_min=90_000,
        salary_max=130_000,
        location="New York",
        remote_ok=False,
        required_skills=["Python", "FastAPI"],
        is_active=True,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job, company, recruiter


@pytest_asyncio.fixture
async def seed_job_high_fit(db: AsyncSession, seed_company) -> tuple[JobListing, Company, Recruiter]:
    """Job that matches seed_candidate well — should clear the 0.60 threshold."""
    company, recruiter = seed_company
    job = JobListing(
        company_id=company.id,
        tenant_id=company.tenant_id,
        title="Backend Engineer",
        min_years_experience=2,        # seed_candidate has 3
        salary_min=70_000,             # overlaps seed_candidate's 80-120k
        salary_max=130_000,
        location="New York",           # matches seed_candidate
        remote_ok=False,
        required_skills=["Python", "FastAPI"],  # both in seed_candidate.skills
        is_active=True,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job, company, recruiter


@pytest_asyncio.fixture
async def seed_job_low_fit(db: AsyncSession, seed_company) -> tuple[JobListing, Company, Recruiter]:
    """Job that will NOT clear the threshold for seed_candidate (fails hard filter)."""
    company, recruiter = seed_company
    job = JobListing(
        company_id=company.id,
        tenant_id=company.tenant_id,
        title="Quantum Physicist",
        min_years_experience=20,       # seed_candidate has 3 — fails hard filter
        salary_min=200_000,
        salary_max=300_000,
        location="Mars",
        remote_ok=False,
        required_skills=["QuantumML", "NeuroSymbolicAI"],
        is_active=True,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job, company, recruiter


@pytest_asyncio.fixture
async def seed_two_companies(db: AsyncSession):
    """Returns two fully-seeded (company, recruiter, jobs) tuples."""
    results = []
    for i in range(2):
        tenant_id = uuid.uuid4()
        company = Company(name=f"Company {i}", tenant_id=tenant_id)
        db.add(company)
        await db.flush()
        recruiter = Recruiter(
            company_id=company.id,
            email=f"recruiter{i}-{uuid.uuid4().hex[:4]}@test.com",
            hashed_password=hash_password("password123"),
            role="owner",
        )
        db.add(recruiter)
        await db.flush()
        jobs = []
        for j in range(2):
            job = JobListing(
                company_id=company.id,
                tenant_id=tenant_id,
                title=f"Job {j} at Company {i}",
                min_years_experience=0,
                is_active=True,
            )
            db.add(job)
            jobs.append(job)
        company.jobs = jobs  # type: ignore[attr-defined]
        company.recruiter = recruiter  # type: ignore[attr-defined]
        results.append(company)
    await db.commit()
    return results
