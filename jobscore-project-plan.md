# Jobscore — swipe-based job matching platform
### Project plan & technical design doc

*(working name — rename freely; used throughout this doc for concreteness)*

---

## 1. Positioning: how this differs from Sorce and the rest

Sorce, Jobloo, and the 2015-era wave (Switch, Jobr, nspHire) all converge on the same model: swipe right, an AI agent auto-applies or auto-submits, and the match itself is a black box. That model optimizes for *volume* — more applications sent, faster. It's also why recruiters increasingly distrust swipe-app traffic: high apply-through rates with low relevance.

Jobscore optimizes for **relevance and trust**, not volume:

| | Sorce / Jobloo | Jobscore |
|---|---|---|
| Match logic | Hidden | Shown as a score breakdown after swipe |
| Application | AI rewrites resume and auto-submits everywhere | User's real profile, only submitted on a genuine mutual match |
| Company side | Passive recipient of bot-tailored resumes | Posts once, only reviews candidates who already cleared the match threshold |
| Rejected swipes | Silent | Candidate optionally sees the skill gap that kept them under threshold |
| Volume control | Unlimited swiping encourages spam-apply | Daily swipe cap per candidate, forces intentionality |
| Trust signal | None — companies get flooded | Companies only see candidates who cleared a real threshold, so every profile in their queue is worth reviewing |

The moat isn't the swipe gesture (that's commodity UI at this point) — it's **explainable, threshold-gated auto-apply that never wastes a recruiter's queue on a bad fit**. That's also the more defensible thing to put on a resume/portfolio, because it's a real systems problem (embeddings, scoring, async pipelines), not a UI trick.

---

## 2. Tech stack

- **Backend:** Python 3.12, FastAPI, SQLModel (SQLAlchemy 2.0 core + Pydantic v2), PostgreSQL 16 with `pgvector`, Alembic, Celery + Redis
- **Frontend:** TypeScript, Next.js 14 (App Router), Tailwind CSS, `framer-motion` for the swipe gesture, TanStack Query for data fetching
- **Auth:** JWT (access + refresh), `passlib`/`bcrypt` for hashing, role + tenant claims embedded in the token
- **Infra:** Docker Compose for local dev, GitHub Actions for CI, deploy target Railway/Render for the portfolio version
- **Testing:** pytest + pytest-asyncio + httpx (backend), Jest + React Testing Library (frontend units), Playwright (e2e)

---

## 3. Repository structure

Monorepo, one Next.js app with route groups rather than two separate frontends — simpler to run and deploy for a project this size, while still cleanly separating the two experiences:

```
jobscore/
├── backend/
│   ├── app/
│   │   ├── main.py                      # FastAPI app factory, router mounting
│   │   ├── core/
│   │   │   ├── config.py                # Settings via pydantic-settings
│   │   │   ├── security.py              # JWT encode/decode, password hashing
│   │   │   └── exceptions.py            # Custom exception classes + handlers
│   │   ├── db/
│   │   │   ├── session.py               # async engine + session factory
│   │   │   ├── base.py                  # declarative base, tenant mixin
│   │   │   └── rls.py                   # sets Postgres session var for RLS
│   │   ├── models/
│   │   │   ├── user.py                  # Candidate
│   │   │   ├── company.py               # Tenant root
│   │   │   ├── job_listing.py
│   │   │   ├── swipe.py
│   │   │   ├── application.py
│   │   │   └── match.py
│   │   ├── schemas/                     # Pydantic request/response models
│   │   ├── api/
│   │   │   ├── deps.py                  # get_current_user, get_current_tenant, role guards
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── candidate/
│   │   │       │   ├── profile.py
│   │   │       │   ├── feed.py          # GET next job cards
│   │   │       │   └── swipe.py         # POST swipe left/right
│   │   │       └── company/
│   │   │           ├── jobs.py          # CRUD job listings
│   │   │           ├── applications.py  # list + PATCH status on auto-matched candidates
│   │   │           └── dashboard.py     # match counts, funnel stats
│   │   ├── services/
│   │   │   ├── embedding_service.py     # wraps sentence-transformers
│   │   │   ├── matching_service.py      # hard filters + weighted score
│   │   │   └── application_service.py   # creates Application automatically once score clears threshold
│   │   ├── workers/
│   │   │   ├── celery_app.py
│   │   │   └── tasks.py                 # recompute_matches_for_candidate, etc.
│   │   └── tests/
│   │       ├── unit/
│   │       │   ├── test_matching_service.py
│   │       │   ├── test_security.py
│   │       │   └── test_schemas.py
│   │       ├── integration/
│   │       │   ├── test_swipe_flow.py
│   │       │   ├── test_tenant_isolation.py
│   │       │   └── test_auth_roles.py
│   │       └── conftest.py              # test DB, fixtures, factory helpers
│   ├── alembic/
│   │   └── versions/
│   ├── pyproject.toml                   # ruff, mypy, pytest config all here
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── (candidate)/
│   │   │   ├── feed/page.tsx            # swipe deck
│   │   │   ├── matches/page.tsx
│   │   │   └── profile/page.tsx
│   │   ├── (company)/
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── jobs/[id]/candidates/page.tsx
│   │   │   └── jobs/new/page.tsx
│   │   └── layout.tsx
│   ├── components/
│   │   ├── swipe/
│   │   │   ├── SwipeCard.tsx
│   │   │   ├── SwipeDeck.tsx
│   │   │   └── SwipeCard.test.tsx
│   │   ├── match/MatchScoreBreakdown.tsx
│   │   └── dashboard/
│   ├── lib/
│   │   ├── api-client.ts                # typed fetch wrapper
│   │   └── types.ts                     # generated from backend OpenAPI schema
│   ├── e2e/
│   │   ├── candidate-swipe-to-match.spec.ts
│   │   └── company-post-job.spec.ts
│   └── package.json
├── docs/
│   ├── architecture.md
│   ├── matching-algorithm.md
│   └── api.md                           # auto-generated from OpenAPI
├── .github/workflows/ci.yml
├── docker-compose.yml
└── README.md
```

Why this layout reads as senior-level rather than tutorial-level: `services/` is separated from `api/` (business logic isn't stuffed in route handlers), tests mirror the source tree 1:1, `core/` isolates cross-cutting concerns, and there's a clean boundary between the ORM models and the Pydantic schemas that cross the wire (never return a raw model from an endpoint).

---

## 4. Data model (core tables)

```
candidates(id, email, hashed_password, name, resume_summary, skills jsonb,
           years_experience, desired_salary_min, desired_salary_max,
           location, remote_ok, profile_embedding vector(384), created_at)

companies(id, name, tenant_id, industry, description, created_at)

recruiters(id, company_id FK -> companies.id, email, hashed_password, role, created_at)
  -- role: "owner" | "recruiter"; company_id is the tenant boundary

job_listings(id, company_id FK, tenant_id, title, description, required_skills jsonb,
             min_years_experience, salary_min, salary_max, location, remote_ok,
             seniority, listing_embedding vector(384), is_active, created_at)

swipes(id, candidate_id FK, job_listing_id FK, direction enum('left','right'), created_at)
  -- candidate-only; unique(candidate_id, job_listing_id)

matches(id, candidate_id FK, job_listing_id FK, score float, score_breakdown jsonb,
        matched_at, status enum('applied','withdrawn'))
  -- created automatically when score >= threshold; no 'pending' state, since
  -- nothing is ever waiting on a company action

applications(id, match_id FK, candidate_id FK, job_listing_id FK,
             status enum('submitted','viewed','rejected','interview'), created_at)
  -- company updates status post-hoc from the dashboard; this update never
  -- blocks or retroactively un-submits the application
```

`tenant_id` lives on every company-owned table (`companies`, `job_listings`, `recruiters` via `companies`, and indirectly on `matches`/`applications` through the FK). Row-Level Security policies scope every query to `current_setting('app.tenant_id')`, which `db/rls.py` sets per-request from the JWT claim — so even a route handler that forgets a `WHERE company_id = ...` clause can't leak across tenants.

---

## 5. Matching algorithm

Two-stage, not a single similarity number. This runs entirely off the candidate's action — the company never swipes to create a match; they post a listing once, and matches land in their dashboard automatically. Their only action is a post-hoc accept/reject on candidates already sitting in that list.

**Stage 1 — hard filters (binary gate).** Reject immediately, before any embedding work runs:
- `candidate.years_experience >= job.min_years_experience`
- location compatible (`remote_ok` on either side, or same metro)
- salary ranges overlap
- work authorization (if collected)

**Stage 2 — weighted soft score**, only computed for candidates that pass Stage 1, triggered the moment the candidate swipes right on a listing:
```
score = 0.5 * cosine_similarity(candidate.profile_embedding, job.listing_embedding)
      + 0.25 * skill_overlap_ratio(candidate.skills, job.required_skills)
      + 0.15 * experience_fit(candidate.years_experience, job.min_years_experience)
      + 0.10 * salary_overlap_ratio(...)
```
Embeddings from `sentence-transformers/all-MiniLM-L6-v2` (384-dim, runs locally, no API cost) capture semantic equivalence ("Next.js" ~ "React") that keyword/Jaccard matching misses. `score_breakdown` (each term's contribution) is stored alongside the total so the UI can render the "why" view rather than just a percentage.

**Threshold: `score >= 0.60` → automatic match.** Crossing the threshold on a candidate's right-swipe does this in one transaction:
1. Writes a `Match` row and creates the `Application` from the candidate's stored profile, with `application.status = 'submitted'`
2. Pushes it into that job listing's dashboard feed for the recruiter to review whenever they next check

**Company-side action happens after the fact, not before it.** From the dashboard, a recruiter can move an `Application` from `submitted` to either `rejected` or `interview` (or leave it untouched — silence isn't a blocking state for anything). There's no "pending on company" status blocking the candidate's application from going out; rejection is a later, non-gating update to an application that already exists.

A right-swipe that doesn't clear 0.60 never surfaces to the company at all — same dead end for the candidate as before.

Full derivation and weight-tuning notes: `docs/matching-algorithm.md`.

---

## 6. API surface (v1)

```
POST   /api/v1/auth/candidate/register
POST   /api/v1/auth/company/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh

GET    /api/v1/candidate/profile
PUT    /api/v1/candidate/profile
GET    /api/v1/candidate/feed              # next N unswiped job cards
POST   /api/v1/candidate/swipe             # {job_listing_id, direction}
GET    /api/v1/candidate/matches
GET    /api/v1/candidate/matches/{id}/breakdown

POST   /api/v1/company/jobs
GET    /api/v1/company/jobs
PATCH  /api/v1/company/jobs/{id}
GET    /api/v1/company/jobs/{id}/applications   # auto-matched candidates for this listing
PATCH  /api/v1/company/applications/{id}        # {status: 'rejected' | 'interview'}
GET    /api/v1/company/dashboard                # match counts, funnel, avg score
```

---

## 7. Testing strategy

Coverage target: 85%+ on `services/` and `api/` (the business-logic-bearing code), not a blanket number on everything.

### 7.1 Backend unit tests (`pytest`, no DB/network)

`tests/unit/test_matching_service.py` — pure logic, mocked embeddings:
```python
import pytest
from app.services.matching_service import compute_match_score, passes_hard_filters
from app.tests.factories import CandidateFactory, JobListingFactory

def test_hard_filter_rejects_under_min_experience():
    candidate = CandidateFactory(years_experience=1)
    job = JobListingFactory(min_years_experience=3)
    assert passes_hard_filters(candidate, job) is False

def test_hard_filter_rejects_salary_no_overlap():
    candidate = CandidateFactory(desired_salary_min=120_000, desired_salary_max=150_000)
    job = JobListingFactory(salary_min=60_000, salary_max=90_000)
    assert passes_hard_filters(candidate, job) is False

def test_hard_filter_passes_remote_mismatch_when_either_side_remote_ok():
    candidate = CandidateFactory(location="Austin", remote_ok=True)
    job = JobListingFactory(location="NYC", remote_ok=False)
    assert passes_hard_filters(candidate, job) is True

@pytest.mark.parametrize("similarity,skill_overlap,exp_fit,salary_overlap,expected", [
    (1.0, 1.0, 1.0, 1.0, 1.0),
    (0.0, 0.0, 0.0, 0.0, 0.0),
    (0.8, 0.5, 1.0, 1.0, pytest.approx(0.775)),
])
def test_score_weighting_is_correct(mocker, similarity, skill_overlap, exp_fit, salary_overlap, expected):
    mocker.patch("app.services.matching_service.cosine_similarity", return_value=similarity)
    mocker.patch("app.services.matching_service.skill_overlap_ratio", return_value=skill_overlap)
    mocker.patch("app.services.matching_service.experience_fit", return_value=exp_fit)
    mocker.patch("app.services.matching_service.salary_overlap_ratio", return_value=salary_overlap)
    score = compute_match_score(CandidateFactory(), JobListingFactory())
    assert score.total == expected

def test_score_at_exact_threshold_boundary_counts_as_match():
    # 0.60 must be inclusive, not exclusive — this is the kind of off-by-one
    # that's easy to get backwards and expensive to get wrong in prod
    from app.services.matching_service import is_match
    assert is_match(0.60) is True
    assert is_match(0.5999) is False

def test_embedding_service_timeout_falls_back_to_keyword_matching(mocker):
    mocker.patch("app.services.embedding_service.encode", side_effect=TimeoutError)
    result = compute_match_score(CandidateFactory(), JobListingFactory())
    assert result.used_fallback is True
```

`tests/unit/test_security.py`:
```python
def test_expired_token_is_rejected():
    token = create_access_token(subject="1", expires_delta=timedelta(seconds=-1))
    with pytest.raises(InvalidTokenError):
        decode_token(token)

def test_token_carries_correct_tenant_and_role_claims():
    token = create_access_token(subject="1", role="recruiter", tenant_id="42")
    payload = decode_token(token)
    assert payload["role"] == "recruiter"
    assert payload["tenant_id"] == "42"
```

### 7.2 Integration tests (`pytest` + test Postgres via `testcontainers` or a Docker Compose test DB)

`tests/integration/test_tenant_isolation.py` — the highest-value test in the whole suite, since a leak here is the worst possible bug in a multi-tenant app:
```python
async def test_recruiter_cannot_see_another_companys_jobs(client, seed_two_companies):
    company_a, company_b = seed_two_companies
    token_a = login_as(company_a.recruiter)
    resp = await client.get("/api/v1/company/jobs", headers=auth_header(token_a))
    returned_ids = {job["id"] for job in resp.json()}
    assert all(j.company_id == company_a.id for j in company_a.jobs)
    assert not returned_ids & {j.id for j in company_b.jobs}

async def test_rls_blocks_raw_query_even_without_orm_filter(db_session, seed_two_companies):
    # Bypass the ORM's WHERE clause on purpose — RLS must still hold
    company_a, company_b = seed_two_companies
    await db_session.execute(text("SET app.tenant_id = :tid"), {"tid": company_a.tenant_id})
    rows = await db_session.execute(text("SELECT * FROM job_listings"))
    assert all(r.company_id == company_a.id for r in rows)
```

`tests/integration/test_swipe_flow.py`:
```python
async def test_right_swipe_above_threshold_auto_creates_match_and_application(client, seed_candidate, seed_job_high_fit):
    token = login_as(seed_candidate)
    await client.post("/api/v1/candidate/swipe",
        json={"job_listing_id": seed_job_high_fit.id, "direction": "right"}, headers=auth_header(token))
    matches = await client.get("/api/v1/candidate/matches", headers=auth_header(token))
    assert seed_job_high_fit.id in [m["job_listing_id"] for m in matches.json()]
    # no company action taken yet — the application already exists
    recruiter_token = login_as(seed_job_high_fit.company.recruiter)
    apps = await client.get(f"/api/v1/company/jobs/{seed_job_high_fit.id}/applications",
        headers=auth_header(recruiter_token))
    assert seed_candidate.id in [a["candidate_id"] for a in apps.json()]
    assert apps.json()[0]["status"] == "submitted"

async def test_right_swipe_below_threshold_never_reaches_company(client, seed_candidate, seed_job_low_fit):
    token = login_as(seed_candidate)
    await client.post("/api/v1/candidate/swipe",
        json={"job_listing_id": seed_job_low_fit.id, "direction": "right"}, headers=auth_header(token))
    matches = await client.get("/api/v1/candidate/matches", headers=auth_header(token))
    assert matches.json() == []
    recruiter_token = login_as(seed_job_low_fit.company.recruiter)
    apps = await client.get(f"/api/v1/company/jobs/{seed_job_low_fit.id}/applications",
        headers=auth_header(recruiter_token))
    assert apps.json() == []

async def test_company_reject_does_not_retract_the_application(client, seed_candidate, seed_job_high_fit):
    token = login_as(seed_candidate)
    await client.post("/api/v1/candidate/swipe",
        json={"job_listing_id": seed_job_high_fit.id, "direction": "right"}, headers=auth_header(token))
    recruiter_token = login_as(seed_job_high_fit.company.recruiter)
    apps = await client.get(f"/api/v1/company/jobs/{seed_job_high_fit.id}/applications",
        headers=auth_header(recruiter_token))
    application_id = apps.json()[0]["id"]
    resp = await client.patch(f"/api/v1/company/applications/{application_id}",
        json={"status": "rejected"}, headers=auth_header(recruiter_token))
    assert resp.status_code == 200
    # candidate's match/application record still exists — rejection is a status
    # update, not a deletion, and never un-submits the application
    matches = await client.get("/api/v1/candidate/matches", headers=auth_header(token))
    assert seed_job_high_fit.id in [m["job_listing_id"] for m in matches.json()]

async def test_recruiter_cannot_move_application_to_arbitrary_status(client, seed_candidate, seed_job_high_fit):
    token = login_as(seed_candidate)
    await client.post("/api/v1/candidate/swipe",
        json={"job_listing_id": seed_job_high_fit.id, "direction": "right"}, headers=auth_header(token))
    recruiter_token = login_as(seed_job_high_fit.company.recruiter)
    apps = await client.get(f"/api/v1/company/jobs/{seed_job_high_fit.id}/applications",
        headers=auth_header(recruiter_token))
    application_id = apps.json()[0]["id"]
    resp = await client.patch(f"/api/v1/company/applications/{application_id}",
        json={"status": "submitted"}, headers=auth_header(recruiter_token))
    assert resp.status_code == 422  # only 'rejected' / 'interview' are valid transitions here

async def test_duplicate_swipe_is_idempotent_not_duplicated(client, seed_candidate, seed_job):
    token = login_as(seed_candidate)
    payload = {"job_listing_id": seed_job.id, "direction": "right"}
    await client.post("/api/v1/candidate/swipe", json=payload, headers=auth_header(token))
    resp = await client.post("/api/v1/candidate/swipe", json=payload, headers=auth_header(token))
    assert resp.status_code == 409  # or idempotent 200 — pick one and test it explicitly

async def test_left_swipe_never_triggers_score_computation(client, seed_candidate, seed_job, mocker):
    spy = mocker.spy(matching_service, "compute_match_score")
    token = login_as(seed_candidate)
    await client.post("/api/v1/candidate/swipe",
        json={"job_listing_id": seed_job.id, "direction": "left"}, headers=auth_header(token))
    spy.assert_not_called()

async def test_daily_swipe_cap_is_enforced(client, seed_candidate, many_jobs):
    token = login_as(seed_candidate)
    for job in many_jobs[:DAILY_SWIPE_CAP]:
        r = await client.post("/api/v1/candidate/swipe",
            json={"job_listing_id": job.id, "direction": "right"}, headers=auth_header(token))
        assert r.status_code == 200
    over_cap = await client.post("/api/v1/candidate/swipe",
        json={"job_listing_id": many_jobs[DAILY_SWIPE_CAP].id, "direction": "right"}, headers=auth_header(token))
    assert over_cap.status_code == 429
```

`tests/integration/test_auth_roles.py`:
```python
async def test_candidate_token_rejected_on_company_only_route(client, seed_candidate):
    token = login_as(seed_candidate)
    resp = await client.post("/api/v1/company/jobs", json={...}, headers=auth_header(token))
    assert resp.status_code == 403

async def test_inactive_job_listing_excluded_from_candidate_feed(client, seed_candidate, inactive_job):
    token = login_as(seed_candidate)
    feed = await client.get("/api/v1/candidate/feed", headers=auth_header(token))
    assert inactive_job.id not in [j["id"] for j in feed.json()]
```

### 7.3 Additional scenarios worth enumerating explicitly (checklist, not all shown as code above)

- Concurrent double-right-swipe race (two requests landing near-simultaneously) doesn't create two `Application` rows — covered by a DB unique constraint + a test that fires both requests concurrently with `asyncio.gather`
- Resume parse failure degrades gracefully to manual profile entry rather than 500ing
- Null salary range on either side doesn't crash `salary_overlap_ratio` (treat as "no constraint," not zero)
- Recruiter removed from a company loses access immediately (token still valid but scope check re-verifies membership, not just the claim)
- Job listing deactivated mid-swipe-session doesn't appear in a candidate's *next* feed page but existing pending matches aren't silently deleted
- Embedding recomputation on profile edit doesn't re-trigger matches for listings already swiped left

### 7.4 Frontend tests

`components/swipe/SwipeCard.test.tsx` (Jest + RTL):
```tsx
test("calls onSwipe('right') when dragged past the right threshold", () => {
  const onSwipe = jest.fn();
  render(<SwipeCard job={mockJob} onSwipe={onSwipe} />);
  const card = screen.getByTestId("swipe-card");
  fireEvent.pointerDown(card, { clientX: 0 });
  fireEvent.pointerMove(card, { clientX: 150 });
  fireEvent.pointerUp(card);
  expect(onSwipe).toHaveBeenCalledWith("right");
});

test("renders salary range and top skill tags on the card", () => {
  render(<SwipeCard job={mockJob} onSwipe={jest.fn()} />);
  expect(screen.getByText(/\$120,000/)).toBeInTheDocument();
  expect(screen.getAllByTestId("skill-tag")).toHaveLength(mockJob.topSkills.length);
});
```

`e2e/candidate-swipe-to-match.spec.ts` (Playwright, against a seeded test backend):
```ts
test("full flow: register, swipe right, get matched, see score breakdown", async ({ page }) => {
  await page.goto("/register");
  await registerCandidate(page, testCandidate);
  await page.goto("/feed");
  await page.getByTestId("swipe-card").dispatchEvent("dragright");
  await expect(page.getByText("It's a match")).toBeVisible();
  await page.getByText("See why").click();
  await expect(page.getByTestId("score-breakdown")).toContainText("Skills");
});
```

### 7.5 CI (`.github/workflows/ci.yml`)

- Backend: `ruff check`, `mypy`, `pytest --cov=app --cov-fail-under=85` against a Postgres service container
- Frontend: `tsc --noEmit`, `eslint`, `jest --coverage`
- E2E: Playwright suite runs against a docker-compose stack, on PR only (not every push, to keep CI fast)
- All four required to pass before merge to `main`

---

## 8. Suggested build order

1. Data model + Alembic migrations + RLS policies (get multi-tenancy right before anything else is built on top of it)
2. `matching_service` with unit tests — pure logic, no DB, fastest feedback loop
3. Auth + role/tenant-scoped `deps.py`
4. Candidate endpoints (profile, feed, swipe) + integration tests
5. Company endpoints (jobs, candidate feed, swipe, dashboard) + integration tests
6. Celery match-recomputation pipeline
7. Frontend swipe deck + match screen
8. Company dashboard
9. E2E suite tying it together
10. Polish: score-breakdown UI, daily swipe cap, empty states

---

## 9. Environment & setup

**Versions:** Python 3.12, Node 20 LTS, PostgreSQL 16, Redis 7.

**Backend dependencies** (`backend/pyproject.toml`):
```toml
[project]
name = "jobscore-backend"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlmodel>=0.0.22",
    "asyncpg>=0.29",
    "alembic>=1.13",
    "pydantic-settings>=2.4",
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
    "celery[redis]>=5.4",
    "sentence-transformers>=3.0",
    "pgvector>=0.3",
    "httpx>=0.27",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2",
    "pytest-asyncio>=0.23",
    "pytest-mock>=3.14",
    "pytest-cov>=5.0",
    "testcontainers[postgres]>=4.7",
    "ruff>=0.5",
    "mypy>=1.10",
]
```

**Frontend dependencies** (`frontend/package.json`, key ones):
```json
{
  "dependencies": {
    "next": "^14.2",
    "react": "^18.3",
    "framer-motion": "^11",
    "@tanstack/react-query": "^5",
    "zod": "^3"
  },
  "devDependencies": {
    "typescript": "^5.5",
    "@playwright/test": "^1.46",
    "jest": "^29",
    "@testing-library/react": "^16",
    "eslint": "^9"
  }
}
```

**`backend/.env.example`:**
```
DATABASE_URL=postgresql+asyncpg://jobscore:jobscore@localhost:5432/jobscore
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=change-me
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
MATCH_SCORE_THRESHOLD=0.60
DAILY_SWIPE_CAP=50
ENVIRONMENT=development
```

**`docker-compose.yml`:**
```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: jobscore
      POSTGRES_PASSWORD: jobscore
      POSTGRES_DB: jobscore
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  backend:
    build: ./backend
    env_file: ./backend/.env
    depends_on: [db, redis]
    ports: ["8000:8000"]
    volumes: ["./backend:/app"]

  worker:
    build: ./backend
    command: celery -A app.workers.celery_app worker --loglevel=info
    env_file: ./backend/.env
    depends_on: [db, redis]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000

volumes:
  pgdata:
```

---

## 10. Non-functional requirements (make these explicit for the agent — they're easy to skip and expensive to retrofit)

- **Error response shape**, consistent across every endpoint:
  ```json
  { "error": { "code": "TENANT_MISMATCH", "message": "...", "field": null } }
  ```
  Implement as a FastAPI exception handler in `core/exceptions.py`, not ad-hoc per route.
- **Pagination:** cursor-based (`?cursor=...&limit=20`) on `feed`, `matches`, and `applications` endpoints — offset pagination breaks once swipes are being written concurrently with reads.
- **Rate limiting:** `DAILY_SWIPE_CAP` enforced server-side per candidate (not just a frontend disable) — return `429` with a `Retry-After` indicating next-midnight-UTC reset.
- **Logging:** structured JSON logs (`structlog` or stdlib `logging` with a JSON formatter), include `tenant_id` and `request_id` on every log line — this is what makes a multi-tenant bug traceable.
- **Idempotency:** `POST /swipe` must be safe to retry — same `(candidate_id, job_listing_id, swiped_by)` returns the existing swipe rather than erroring or duplicating, except where the design doc above says to test for `409` explicitly (pick one behavior and keep the docstring, tests, and implementation in agreement).
- **Migrations:** every schema change goes through an Alembic revision, never a manual `ALTER TABLE` — the agent should run `alembic revision --autogenerate` and review the diff before applying.
- **Secrets:** nothing in `.env.example` should contain a real secret; `JWT_SECRET_KEY` in particular must be generated fresh per environment, never committed.

---

## 11. Definition of done, per build-order phase

Use this as the acceptance checklist for each phase in Section 8 before moving to the next one — an agent working through this doc should treat each phase as blocked until its checklist passes.

**Phase 1 — Data model + RLS**
- [ ] All tables in Section 4 exist via Alembic migration, not raw SQL
- [ ] RLS policy on every tenant-scoped table; `test_rls_blocks_raw_query_even_without_orm_filter` passes
- [ ] `pgvector` extension enabled, `vector(384)` columns present

**Phase 2 — Matching service**
- [ ] All tests in `tests/unit/test_matching_service.py` pass, including the threshold-boundary test
- [ ] `score_breakdown` is returned alongside `total` for every computed score
- [ ] Embedding timeout falls back without raising

**Phase 3 — Auth**
- [ ] JWT carries `role` and `tenant_id`; `test_security.py` passes
- [ ] Candidate token rejected on company-only routes (403, not 401)

**Phase 4 — Candidate endpoints**
- [ ] Feed excludes already-swiped and inactive listings
- [ ] Swipe endpoint enforces `DAILY_SWIPE_CAP` and idempotency
- [ ] `test_swipe_flow.py` passes in full

**Phase 5 — Company endpoints**
- [ ] Dashboard returns match count, funnel (swiped → matched → applied), avg score — all scoped to the requesting tenant only
- [ ] `test_tenant_isolation.py` passes in full

**Phase 6 — Celery pipeline**
- [ ] Profile/listing edit triggers async recompute, doesn't block the request
- [ ] Recompute doesn't resurrect a match on a listing already swiped left by either side

**Phase 7–8 — Frontend**
- [ ] `SwipeCard.test.tsx` passes; drag-threshold logic covered
- [ ] Score breakdown renders all four weighted components from Section 5

**Phase 9 — E2E**
- [ ] `candidate-swipe-to-match.spec.ts` and `company-post-job.spec.ts` both pass against the docker-compose stack

**Phase 10 — Polish**
- [ ] Empty states for zero-match feed, zero dashboard data
- [ ] `pytest --cov=app --cov-fail-under=85` passes

---

## 12. What to say about this project on a resume/portfolio

Frame it around the systems decisions, not the swipe gimmick: "Designed and built a multi-tenant job-matching platform with row-level-security tenant isolation, an embedding-based match-scoring pipeline (pgvector + sentence-transformers) with async recomputation via Celery, and 85%+ test coverage including tenant-isolation and race-condition integration tests." That sentence does more work in an interview than "built a Tinder for jobs."