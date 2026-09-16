from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.swipe import Swipe
    from app.models.match import Match


class Candidate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "candidates"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    resume_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, default=list)
    years_experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    desired_salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    desired_salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remote_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    profile_embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)

    swipes: Mapped[list["Swipe"]] = relationship("Swipe", back_populates="candidate")
    matches: Mapped[list["Match"]] = relationship("Match", back_populates="candidate")
