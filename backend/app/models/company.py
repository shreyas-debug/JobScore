from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, TenantMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job_listing import JobListing


class Company(Base, UUIDMixin, TenantMixin, TimestampMixin):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    recruiters: Mapped[list["Recruiter"]] = relationship("Recruiter", back_populates="company")
    job_listings: Mapped[list["JobListing"]] = relationship("JobListing", back_populates="company")


class Recruiter(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "recruiters"

    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="recruiter")
    # role: "owner" | "recruiter"

    company: Mapped["Company"] = relationship("Company", back_populates="recruiters")
