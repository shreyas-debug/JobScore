from __future__ import annotations

import uuid
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.match import Match


class ApplicationStatus(str, PyEnum):
    submitted = "submitted"
    viewed = "viewed"
    rejected = "rejected"
    interview = "interview"


class Application(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "applications"
    __table_args__ = (
        # Race-condition guard: two concurrent right-swipes can't create two applications
        UniqueConstraint("candidate_id", "job_listing_id", name="uq_application_pair"),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id"), nullable=False, index=True)
    job_listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_listings.id"), nullable=False, index=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), nullable=False, default=ApplicationStatus.submitted
    )

    match: Mapped["Match"] = relationship("Match", back_populates="application")
