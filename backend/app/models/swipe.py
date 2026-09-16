from __future__ import annotations

import uuid
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import Candidate
    from app.models.job_listing import JobListing


class SwipeDirection(str, PyEnum):
    left = "left"
    right = "right"


class Swipe(Base, UUIDMixin, TimestampMixin):
    """Candidate-only swipe — the company no longer swipes back.

    unique(candidate_id, job_listing_id) prevents duplicate swipes.
    """
    __tablename__ = "swipes"
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_listing_id", name="uq_swipe_pair"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id"), nullable=False, index=True)
    job_listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_listings.id"), nullable=False, index=True)
    direction: Mapped[SwipeDirection] = mapped_column(Enum(SwipeDirection), nullable=False)

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="swipes")
    job_listing: Mapped["JobListing"] = relationship("JobListing", back_populates="swipes")
