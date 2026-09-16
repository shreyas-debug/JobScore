from __future__ import annotations

import uuid
from enum import Enum as PyEnum
from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import Enum, Float, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import Candidate
    from app.models.job_listing import JobListing


class MatchStatus(str, PyEnum):
    applied = "applied"      # Match crossed threshold — application auto-submitted
    withdrawn = "withdrawn"  # Candidate withdrew


class Match(Base, UUIDMixin, TimestampMixin):
    """Created automatically when a candidate's right-swipe scores >= threshold.

    No 'pending' status — there is nothing waiting on a company action.
    The application already exists the moment this row is written.
    """
    __tablename__ = "matches"

    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id"), nullable=False, index=True)
    job_listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_listings.id"), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    score_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus), nullable=False, default=MatchStatus.applied)

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="matches")
    job_listing: Mapped["JobListing"] = relationship("JobListing", back_populates="matches")
    application: Mapped["Application | None"] = relationship("Application", back_populates="match", uselist=False)
