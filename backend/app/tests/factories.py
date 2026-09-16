from __future__ import annotations

import dataclasses
import uuid
from typing import Any


@dataclasses.dataclass
class CandidateFactory:
    """Lightweight in-memory candidate for unit tests — no DB needed."""

    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)
    email: str = "candidate@example.com"
    name: str = "Test Candidate"
    years_experience: int = 3
    desired_salary_min: int | None = 80_000
    desired_salary_max: int | None = 120_000
    location: str = "New York"
    remote_ok: bool = False
    skills: list[str] = dataclasses.field(default_factory=lambda: ["Python", "FastAPI", "PostgreSQL"])
    profile_embedding: list[float] | None = None


@dataclasses.dataclass
class JobListingFactory:
    """Lightweight in-memory job listing for unit tests — no DB needed."""

    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)
    title: str = "Backend Engineer"
    min_years_experience: int = 2
    salary_min: int | None = 90_000
    salary_max: int | None = 130_000
    location: str = "New York"
    remote_ok: bool = False
    required_skills: list[str] = dataclasses.field(default_factory=lambda: ["Python", "FastAPI", "Docker"])
    listing_embedding: list[float] | None = None
