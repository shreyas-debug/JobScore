from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── helper type aliases ────────────────────────────────────────────────────


@dataclass
class MatchScore:
    total: float
    embedding_similarity: float
    skill_overlap: float
    experience_fit: float
    salary_overlap: float
    used_fallback: bool = False

    @property
    def breakdown(self) -> dict[str, float]:
        return {
            "embedding_similarity": round(self.embedding_similarity, 4),
            "skill_overlap": round(self.skill_overlap, 4),
            "experience_fit": round(self.experience_fit, 4),
            "salary_overlap": round(self.salary_overlap, 4),
            "total": round(self.total, 4),
        }


# ── pure helper functions (easily mockable in unit tests) ─────────────────


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Cosine similarity between two equal-length vectors.

    Returns 0.0 if either vector is None or all-zeros.
    """
    if not vec_a or not vec_b:
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def skill_overlap_ratio(candidate_skills: list[str], required_skills: list[str]) -> float:
    """Jaccard-style overlap: intersection / len(required_skills).

    Normalizes to lowercase for comparison. Treats None / empty as 0.
    If required_skills is empty, returns 1.0 (no hard requirement → perfect fit).

    Also handles the case where skills were stored as a single comma-separated
    string (e.g. ["React, TypeScript, Python"]) by expanding them before comparison.
    """
    if not required_skills:
        return 1.0
    if not candidate_skills:
        return 0.0

    # Expand any comma-concatenated entries (handles legacy corrupt data gracefully)
    expanded_c: set[str] = set()
    for s in candidate_skills:
        for part in s.split(","):
            clean = part.strip().lower()
            if clean:
                expanded_c.add(clean)

    r = {s.lower() for s in required_skills}
    return len(expanded_c & r) / len(r)


def experience_fit(candidate_years: int, min_years: int) -> float:
    """Capped linear fit: 1.0 if candidate meets or exceeds minimum.

    Partial credit for candidates who are close: a candidate with 2 years
    applying to a 3-year role scores 2/3 ≈ 0.67 instead of 0.
    """
    if min_years <= 0:
        return 1.0
    return min(1.0, candidate_years / min_years)


def salary_overlap_ratio(
    c_min: int | None,
    c_max: int | None,
    j_min: int | None,
    j_max: int | None,
) -> float:
    """Proportion of overlap relative to the narrower range.

    Treats None salary on either side as "no constraint" → full overlap.
    Returns 0.0 only when the ranges are disjoint with no null values.
    """
    if c_min is None or c_max is None or j_min is None or j_max is None:
        return 1.0
    overlap_start = max(c_min, j_min)
    overlap_end = min(c_max, j_max)
    if overlap_start > overlap_end:
        return 0.0
    overlap = overlap_end - overlap_start
    narrower = min(c_max - c_min, j_max - j_min)
    if narrower == 0:
        return 1.0
    return min(1.0, overlap / narrower)


# ── hard filters ──────────────────────────────────────────────────────────


def passes_hard_filters(candidate: Any, job: Any) -> bool:
    """Binary gate — must pass all checks before soft scoring runs.

    Accepts any object / dataclass with the required attributes so this
    remains pure and unit-testable without touching the DB.
    """
    # 1. Experience
    if candidate.years_experience < job.min_years_experience:
        return False

    # 2. Location / remote
    c_remote = getattr(candidate, "remote_ok", False)
    j_remote = getattr(job, "remote_ok", False)
    if not c_remote and not j_remote:
        # Both require physical presence — locations must match
        c_loc = (getattr(candidate, "location", "") or "").lower().strip()
        j_loc = (getattr(job, "location", "") or "").lower().strip()
        if c_loc and j_loc and c_loc != j_loc:
            return False

    # 3. Salary overlap — None means no constraint
    c_min = getattr(candidate, "desired_salary_min", None)
    c_max = getattr(candidate, "desired_salary_max", None)
    j_min = getattr(job, "salary_min", None)
    j_max = getattr(job, "salary_max", None)
    if None not in (c_min, c_max, j_min, j_max):
        if c_min > j_max or j_min > c_max:  # type: ignore[operator]
            return False

    return True


# ── soft score ────────────────────────────────────────────────────────────


def compute_match_score(candidate: Any, job: Any) -> MatchScore:
    """Two-stage matching: hard filters are the caller's responsibility.

    Weights (must sum to 1.0):
        0.50  cosine_similarity(embeddings)
        0.25  skill_overlap_ratio
        0.15  experience_fit
        0.10  salary_overlap_ratio
    """
    from app import services as _svc_module  # local import to allow mocking

    used_fallback = False

    # --- embedding similarity ---
    c_emb = getattr(candidate, "profile_embedding", None) or []
    j_emb = getattr(job, "listing_embedding", None) or []

    if not c_emb or not j_emb:
        # Honest fallback: If embeddings are missing, we just use skill overlap.
        # We don't pretend to retry embedding generation synchronously.
        c_skills = getattr(candidate, "skills", []) or []
        j_skills = getattr(job, "required_skills", []) or []
        sim = skill_overlap_ratio(c_skills, j_skills)
        used_fallback = True
    else:
        sim = cosine_similarity(c_emb, j_emb)

    # --- skill overlap ---
    c_skills = getattr(candidate, "skills", []) or []
    j_skills = getattr(job, "required_skills", []) or []
    sk = skill_overlap_ratio(list(c_skills), list(j_skills))

    # --- experience fit ---
    exp = experience_fit(
        getattr(candidate, "years_experience", 0),
        getattr(job, "min_years_experience", 0),
    )

    # --- salary overlap ---
    sal = salary_overlap_ratio(
        getattr(candidate, "desired_salary_min", None),
        getattr(candidate, "desired_salary_max", None),
        getattr(job, "salary_min", None),
        getattr(job, "salary_max", None),
    )

    total = 0.50 * sim + 0.25 * sk + 0.15 * exp + 0.10 * sal

    return MatchScore(
        total=round(total, 6),
        embedding_similarity=sim,
        skill_overlap=sk,
        experience_fit=exp,
        salary_overlap=sal,
        used_fallback=used_fallback,
    )


def is_match(score: float) -> bool:
    """Threshold is inclusive at 0.60."""
    return score >= settings.MATCH_SCORE_THRESHOLD
