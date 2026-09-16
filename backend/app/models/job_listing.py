from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, TenantMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.swipe import Swipe
    from app.models.match import Match


class JobListing(Base, UUIDMixin, TenantMixin, TimestampMixin):
    __tablename__ = "job_listings"

    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_skills: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, default=list)
    min_years_experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remote_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    seniority: Mapped[str | None] = mapped_column(String(100), nullable=True)
    listing_embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    company: Mapped["Company"] = relationship("Company", back_populates="job_listings")
    swipes: Mapped[list["Swipe"]] = relationship("Swipe", back_populates="job_listing")
    matches: Mapped[list["Match"]] = relationship("Match", back_populates="job_listing")
