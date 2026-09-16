from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_candidate
from app.core.exceptions import NotFoundError
from app.db.session import get_session
from app.models.user import Candidate
from app.schemas import CandidateProfileResponse, CandidateProfileUpdate

router = APIRouter(prefix="/candidate/profile", tags=["candidate"])


@router.get("", response_model=CandidateProfileResponse)
async def get_profile(
    payload: Annotated[dict, Depends(get_current_candidate)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> CandidateProfileResponse:
    candidate = await db.get(Candidate, uuid.UUID(payload["sub"]))
    if not candidate:
        raise NotFoundError("Candidate not found.")
    return CandidateProfileResponse.model_validate(candidate)


@router.put("", response_model=CandidateProfileResponse)
async def update_profile(
    body: CandidateProfileUpdate,
    payload: Annotated[dict, Depends(get_current_candidate)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> CandidateProfileResponse:
    candidate = await db.get(Candidate, uuid.UUID(payload["sub"]))
    if not candidate:
        raise NotFoundError("Candidate not found.")

    # Normalize skills: split any comma-separated strings into individual entries
    if body.skills is not None:
        normalized: list[str] = []
        for s in body.skills:
            for part in s.split(","):
                clean = part.strip()
                if clean and clean not in normalized:
                    normalized.append(clean)
        body = body.model_copy(update={"skills": normalized})

    for field_name, value in body.model_dump(exclude_none=True).items():
        setattr(candidate, field_name, value)

    # ── reset swipes / matches so candidate can match again with new skills ──
    from app.models.application import Application
    from app.models.match import Match
    from app.models.swipe import Swipe
    from sqlalchemy import delete

    await db.execute(delete(Application).where(Application.candidate_id == candidate.id))
    await db.execute(delete(Match).where(Match.candidate_id == candidate.id))
    await db.execute(delete(Swipe).where(Swipe.candidate_id == candidate.id))

    await db.commit()
    await db.refresh(candidate)

    # Queue embedding generation in the background (non-blocking)
    if body.skills is not None or body.resume_summary is not None:
        text = f"{candidate.resume_summary or ''} {' '.join(candidate.skills or [])}"
        text = text.strip()
        if text:
            try:
                from app.workers.tasks import update_candidate_embedding
                update_candidate_embedding.delay(str(candidate.id), text)
            except Exception:
                pass  # Celery not available — embedding will be computed later

    return CandidateProfileResponse.model_validate(candidate)
