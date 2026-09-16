# Matching Algorithm

## Overview

Two-stage pipeline. Hard filters run first (O(1) per candidate per job).
Soft scoring only runs for candidates that pass all gates.

**Trigger:** The moment a candidate swipes right on a listing. No company action is needed to initiate scoring.

## Stage 1 — Hard Filters

Binary gate — fail any → reject immediately, no embedding work done.

| Filter | Rule |
|--------|------|
| Experience | `candidate.years_experience >= job.min_years_experience` |
| Location | Either side `remote_ok = true`, or locations match |
| Salary | Ranges must overlap, or either side has NULL (no constraint) |

## Stage 2 — Weighted Soft Score

```
score = 0.50 × cosine_similarity(candidate.profile_embedding, job.listing_embedding)
      + 0.25 × skill_overlap_ratio(candidate.skills, job.required_skills)
      + 0.15 × experience_fit(candidate.years_experience, job.min_years_experience)
      + 0.10 × salary_overlap_ratio(...)
```

### Embeddings (50%)

Model: `sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions, normalized.

Runs locally — no API cost or rate limits. Captures semantic equivalence (e.g. "Next.js" ~ "React framework") that keyword matching misses.

On timeout or failure: falls back to `skill_overlap_ratio` for the embedding term. `score.used_fallback = True` is stored.

### Skill Overlap (25%)

`len(candidate_skills ∩ required_skills) / len(required_skills)`

Normalized to lowercase. Empty `required_skills` → 1.0 (no hard requirement).

### Experience Fit (15%)

`min(1.0, candidate.years_experience / job.min_years_experience)`

Partial credit for near-matches. Zero min_years → 1.0.

### Salary Overlap (10%)

`overlap_range / min(candidate_range, job_range)`

NULL on either side → 1.0. Disjoint ranges → 0.0.

## Threshold & Match Creation

`score >= 0.60` is the match gate — **inclusive**.

When a right-swipe clears the threshold, in a **single atomic transaction**:
1. A `Match` row is written with `status = 'applied'` and the full `score_breakdown`.
2. An `Application` row is written with `status = 'submitted'`.
3. The application immediately appears in the recruiter's dashboard for that listing.

**No company action is needed to create the match.** The company-side dashboard is purely post-hoc: recruiters can move an application from `submitted` to `rejected` or `interview`. That status update never retracts or deletes the application.

A right-swipe below 0.60 is recorded as a swipe but creates no Match or Application — it never surfaces to the company at all.

## `score_breakdown` JSON

Stored alongside `score` in the `matches` table for the "See why" UI:

```json
{
  "embedding_similarity": 0.82,
  "skill_overlap": 0.67,
  "experience_fit": 1.0,
  "salary_overlap": 0.9,
  "total": 0.82
}
```

## Weight Tuning

Current weights are a baseline. With enough match → outcome data (application moved to interview, offer made), these can be tuned via ridge regression on `outcome ~ breakdown_components`.
