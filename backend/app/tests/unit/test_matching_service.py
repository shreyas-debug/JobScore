from __future__ import annotations

import pytest

from app.services.matching_service import (
    compute_match_score,
    cosine_similarity,
    experience_fit,
    is_match,
    passes_hard_filters,
    salary_overlap_ratio,
    skill_overlap_ratio,
)
from app.tests.factories import CandidateFactory, JobListingFactory


# ── hard filter tests ─────────────────────────────────────────────────────


def test_hard_filter_rejects_under_min_experience():
    candidate = CandidateFactory(years_experience=1)
    job = JobListingFactory(min_years_experience=3)
    assert passes_hard_filters(candidate, job) is False


def test_hard_filter_passes_at_exact_experience():
    candidate = CandidateFactory(years_experience=3)
    job = JobListingFactory(min_years_experience=3)
    assert passes_hard_filters(candidate, job) is True


def test_hard_filter_rejects_salary_no_overlap():
    candidate = CandidateFactory(desired_salary_min=120_000, desired_salary_max=150_000)
    job = JobListingFactory(salary_min=60_000, salary_max=90_000)
    assert passes_hard_filters(candidate, job) is False


def test_hard_filter_passes_remote_mismatch_when_either_side_remote_ok():
    candidate = CandidateFactory(location="Austin", remote_ok=True)
    job = JobListingFactory(location="NYC", remote_ok=False)
    assert passes_hard_filters(candidate, job) is True


def test_hard_filter_rejects_location_mismatch_both_onsite():
    candidate = CandidateFactory(location="Austin", remote_ok=False)
    job = JobListingFactory(location="NYC", remote_ok=False)
    assert passes_hard_filters(candidate, job) is False


def test_hard_filter_passes_null_salary_on_either_side():
    candidate = CandidateFactory(desired_salary_min=None, desired_salary_max=None)
    job = JobListingFactory(salary_min=60_000, salary_max=90_000)
    assert passes_hard_filters(candidate, job) is True


# ── score weighting tests ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    "similarity,skill_overlap,exp_fit,salary_overlap,expected",
    [
        (1.0, 1.0, 1.0, 1.0, 1.0),
        (0.0, 0.0, 0.0, 0.0, 0.0),
        (0.8, 0.5, 1.0, 1.0, pytest.approx(0.775)),
    ],
)
def test_score_weighting_is_correct(mocker, similarity, skill_overlap, exp_fit, salary_overlap, expected):
    mocker.patch("app.services.matching_service.cosine_similarity", return_value=similarity)
    mocker.patch("app.services.matching_service.skill_overlap_ratio", return_value=skill_overlap)
    mocker.patch("app.services.matching_service.experience_fit", return_value=exp_fit)
    mocker.patch("app.services.matching_service.salary_overlap_ratio", return_value=salary_overlap)
    # Provide embeddings so the embedding branch is taken (won't actually compute — cosine_similarity is mocked)
    c = CandidateFactory(profile_embedding=[0.1] * 384)
    j = JobListingFactory(listing_embedding=[0.1] * 384)
    score = compute_match_score(c, j)
    assert score.total == expected


def test_score_at_exact_threshold_boundary_counts_as_match():
    # 0.60 must be inclusive, not exclusive
    assert is_match(0.60) is True
    assert is_match(0.5999) is False


def test_embedding_service_timeout_falls_back_to_keyword_matching(mocker):
    mocker.patch("app.services.embedding_service.encode", side_effect=TimeoutError)
    # No embeddings → will hit fallback path in compute_match_score
    candidate = CandidateFactory(profile_embedding=None)
    job = JobListingFactory(listing_embedding=None)
    result = compute_match_score(candidate, job)
    assert result.used_fallback is True


# ── helper function unit tests ────────────────────────────────────────────


def test_skill_overlap_ratio_full_match():
    assert skill_overlap_ratio(["Python", "FastAPI"], ["Python", "FastAPI"]) == 1.0


def test_skill_overlap_ratio_partial():
    assert skill_overlap_ratio(["Python"], ["Python", "Docker"]) == pytest.approx(0.5)


def test_skill_overlap_ratio_empty_required_is_full_match():
    assert skill_overlap_ratio(["Python"], []) == 1.0


def test_skill_overlap_ratio_case_insensitive():
    assert skill_overlap_ratio(["python"], ["Python"]) == 1.0


def test_experience_fit_above_min_is_1():
    assert experience_fit(5, 3) == 1.0


def test_experience_fit_partial_credit():
    assert experience_fit(2, 4) == pytest.approx(0.5)


def test_salary_overlap_null_is_full():
    assert salary_overlap_ratio(None, None, 80_000, 120_000) == 1.0


def test_salary_overlap_disjoint_is_zero():
    assert salary_overlap_ratio(50_000, 70_000, 100_000, 130_000) == 0.0


def test_cosine_similarity_identical_vectors():
    v = [1.0, 0.0, 0.0]
    assert cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_empty_returns_zero():
    assert cosine_similarity([], [1.0, 0.0]) == 0.0


def test_score_breakdown_contains_all_four_components():
    c = CandidateFactory(profile_embedding=[0.1] * 384)
    j = JobListingFactory(listing_embedding=[0.1] * 384)
    score = compute_match_score(c, j)
    breakdown = score.breakdown
    assert "embedding_similarity" in breakdown
    assert "skill_overlap" in breakdown
    assert "experience_fit" in breakdown
    assert "salary_overlap" in breakdown
    assert "total" in breakdown
