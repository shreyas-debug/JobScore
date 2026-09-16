# Jobscore

**Swipe-based job matching with explainable scores.** Candidates fill out their skills and preferences, then swipe on curated job cards. A match is triggered when a candidate swipes right *and* the computed match score clears the threshold — with every match showing a precise breakdown of exactly why it scored that number.

---

## What makes this different

| | Typical job boards | Jobscore |
|---|---|---|
| Match logic | Hidden / algorithmic black box | Fully transparent: weighted skill overlap, experience fit, salary alignment, semantic similarity |
| Application | Auto-apply spam everywhere | Submitted **only** on a verified match — score must clear the threshold |
| Signal quality | Mass-apply noise | Daily swipe cap (50/day) forces intentional choices |
| Speed | Minutes to a result | Match result and score breakdown returned **instantly** on swipe |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy async, asyncpg, Alembic |
| Database | PostgreSQL 16 + pgvector (vector similarity search) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` — local, no API cost |
| Task queue | Celery + Redis (async embedding generation & match recomputation) |
| Auth | JWT (access + refresh tokens), bcrypt via `asyncio.to_thread` (non-blocking) |
| Multi-tenancy | `tenant_id` column isolation on all company-side tables |
| Frontend | TypeScript, Next.js 14 (App Router), Framer Motion, Pure CSS (custom properties), Minimalist Design |
| Containerization | Docker Compose (db, redis, backend, worker, frontend) |

---

## Quick Start

### With Docker Compose (recommended)

```bash
git clone https://github.com/shreyas-debug/JobScore.git
cd JobScore

# Start everything — migrations, seed data, and dev servers all run automatically
docker compose up
```

- **Frontend:** http://localhost:3000  
- **Backend API:** http://localhost:8000  
- **Swagger docs:** http://localhost:8000/docs

The `backend` service automatically runs `alembic upgrade head && python seed_data.py` on startup, so the database is pre-populated with 20 companies and 30+ job listings.

### Local Development (without Docker)

```bash
# 1. Backend
cd backend
pip install -e ".[dev]"
cp .env.example .env        # set JWT_SECRET_KEY and DATABASE_URL

alembic upgrade head
python seed_data.py
uvicorn app.main:app --reload --port 8000

# 2. Celery worker (separate terminal — needed for embedding generation)
celery -A app.workers.celery_app worker --loglevel=info

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## How Matching Works

### Two-Stage Pipeline

**Stage 1 — Hard Filters** (binary gate, any failure excludes the job entirely):
- Candidate's years of experience < job's minimum requirement
- Neither side is remote-ok and their locations differ
- Salary ranges are completely non-overlapping
- Candidate matches **zero** required-level skills on the listing

**Stage 2 — Soft Scoring** (runs only on jobs that pass all hard filters):

```
total = 0.50 × embedding_similarity
      + 0.25 × skill_overlap (weighted)
      + 0.15 × experience_fit
      + 0.10 × salary_overlap
```

### Weighted Skill Scoring

Skills on every job listing are tagged as **required** or **preferred**. The skill overlap term is computed as a weighted blend rather than a flat ratio:

```
skill_overlap = 0.75 × (required_skills_matched / total_required)
              + 0.25 × (preferred_skills_matched / total_preferred)
```

This means a candidate who covers all the dealbreaker skills but lacks nice-to-haves scores significantly higher than one who has the nice-to-haves but misses the hard requirements. The weighting constants (`REQUIRED_SKILL_WEIGHT`, `PREFERRED_SKILL_WEIGHT`) are exposed in config so they can be tuned without a redeploy.

### Embedding Similarity

`all-MiniLM-L6-v2` encodes the candidate's resume summary + skills and the job's description + skill list into 384-dimensional dense vectors. Cosine similarity between these vectors captures semantic equivalence ("Next.js" ≈ "React") that plain keyword matching misses.

Embeddings are generated asynchronously by the Celery worker after profile creation or update. If vectors aren't ready yet, the embedding term falls back to a **neutral 0.5 baseline** (not zero) so the skill overlap and experience terms carry the score correctly rather than being dragged down by a missing component.

### Match Threshold

A match fires when `total >= 0.35`. The threshold is configurable via `MATCH_SCORE_THRESHOLD` in config without a code change.

### Score Breakdown

Every match record stores `score_breakdown` as a JSON dict with all four component scores and the total — so the UI can display exactly which dimension contributed what, making the score fully auditable and not a black box.

---

## User Flows

### Candidate Flow
1. **Register** → `/register/candidate`
2. **Set preferences** → `/onboarding` (skills, experience, salary range, location)
3. **Swipe** → `/feed` — drag cards left/right, click to flip card for full details, or use arrow keys
4. **Match fires** → instant celebration modal with score breakdown
5. **View matches** → `/matches`
6. **Update profile** → `/profile` → auto-redirects back to feed

### Recruiter Flow
1. **Register company** → `/register/company`
2. **Post jobs** → `/jobs/new` — tag each skill as **Required** or **Preferred** with a toggle
3. **Review matched candidates** → `/jobs/[id]/candidates`
4. **Update application status** → accept for interview / reject

---

## Seeded Companies & Jobs

20 companies and 30+ roles are pre-loaded across a range of sectors:

| Company | Industry | Role |
|---------|----------|------|
| Supastack Cloud | Developer Tools & Cloud | Senior Full-Stack Engineer, Staff Distributed Systems Engineer |
| NeuralPath AI | Artificial Intelligence | AI Platform Engineer, Machine Learning Engineer |
| FinPulse Global | FinTech | Senior Backend Architect, Frontend Engineer (Design Systems) |
| Veloce Health | HealthTech | Full-Stack Software Engineer |
| HyperScale Networks | Cybersecurity & Infra | DevOps & Infrastructure Engineer |
| Prism Robotics | Robotics & Hardware | Computer Vision & ML Engineer |
| Aether Commerce | E-Commerce & Retail | Principal Web Performance Engineer |
| Chronos Analytics | Data & Analytics | Lead Data Platform Engineer |
| OpenForge Studio | Gaming & Web3 | Multiplayer Gameplay Engineer |
| Beacon Security | Cybersecurity | Application Security Engineer |
| Lumina Creative | Creative Tools | Frontend Graphics Engineer |
| Kite Logistics | Supply Chain & Logistics | Operations Systems Engineer |
| Golang Gateway | FinTech | Backend Engineer (Go) |
| C-Sharp Innovations | Enterprise Software | .NET Developer |
| Flowdesk | SaaS & Productivity | Full-Stack Product Engineer, Backend Engineer (Integrations) |
| SkillBridge Academy | EdTech | Platform Engineer |
| CarbonGrid | ClimateTech | Data Infrastructure Engineer |
| WaveStream | Media & Entertainment | Streaming Backend Engineer, React Frontend Engineer |
| CodeLens | Developer Tools | Backend Engineer (Analysis Engine) |
| Depot Marketplace | Marketplace & B2B | Fullstack Engineer |

---

## Repository Structure

```
jobscore/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI routers (auth, candidate, company)
│   │   ├── core/            # Config, security, exceptions
│   │   ├── db/              # SQLAlchemy session, base model
│   │   ├── models/          # ORM models (Candidate, JobListing, Match, ...)
│   │   ├── schemas/         # Pydantic request/response schemas (incl. SkillRequirement)
│   │   ├── services/        # matching_service, embedding_service, application_service
│   │   └── workers/         # Celery tasks (embedding generation, match recomputation)
│   ├── alembic/             # Database migrations
│   └── seed_data.py         # 20 companies × 30+ jobs with required/preferred skill tiers
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   │   ├── (candidate)/     # Feed, matches, profile, onboarding
│   │   └── (company)/       # Dashboard, jobs, candidates
│   ├── components/          # SwipeDeck, SwipeCard (3D flip), MatchScoreBreakdown, Navbar
│   ├── context/             # AuthContext (JWT decode, token refresh)
│   └── lib/                 # api-client.ts, types.ts (SkillRequirement type)
├── docs/                    # Architecture and matching algorithm deep-dives
└── docker-compose.yml
```

---

## Running Tests

```bash
# Backend
cd backend
pytest --cov=app --cov-fail-under=85

# Frontend unit tests
cd frontend
npm test
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for Celery broker/backend |
| `JWT_SECRET_KEY` | `change-me` | **Change this in production** |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `MATCH_SCORE_THRESHOLD` | `0.35` | Minimum score to trigger a match |
| `REQUIRED_SKILL_WEIGHT` | `0.75` | Weight of required-level skills in skill overlap scoring |
| `PREFERRED_SKILL_WEIGHT` | `0.25` | Weight of preferred-level skills in skill overlap scoring |
| `DAILY_SWIPE_CAP` | `50` | Max swipes per candidate per day |
