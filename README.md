# Jobscore

**Swipe-based job matching with explainable scores.** Candidates fill out their skills and preferences, then swipe on curated job cards. A match is triggered when a candidate swipes right *and* the computed match score clears the threshold — with every match showing a precise breakdown of exactly why it scored that number.

---

## What makes this different

| | Typical job boards | Jobscore |
|---|---|---|
| Match logic | Hidden / algorithmic black box | Fully transparent: skill overlap, experience fit, salary alignment, semantic similarity |
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
git clone <repo>
cd jobscore

# Start everything — migrations, seed data, and dev servers all run automatically
docker compose up
```

- **Frontend:** http://localhost:3000  
- **Backend API:** http://localhost:8000  
- **Swagger docs:** http://localhost:8000/docs

The `backend` service automatically runs `alembic upgrade head && python seed_data.py` on startup, so the database is pre-populated with 14 companies and 18 job listings.

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

### Scoring Formula

```
total = 0.50 × embedding_similarity
      + 0.25 × skill_overlap
      + 0.15 × experience_fit
      + 0.10 × salary_overlap
```

**Hard filters** run first (a job is excluded from the deck entirely if):
- Candidate's years of experience < job's minimum requirement
- Neither side is remote-ok and their locations differ
- Salary ranges are completely non-overlapping

If the candidate has no profile yet, hard filters are skipped and all jobs are shown so new users always see a populated deck.

**Embedding similarity** uses `all-MiniLM-L6-v2` to semantically compare the candidate's summary+skills against the job description. Since embeddings are generated asynchronously by the Celery worker, the system falls back to skill overlap if embeddings aren't ready yet.

A match fires when `total >= 0.40`.

---

## User Flows

### Candidate Flow
1. **Register** → `/register/candidate`
2. **Set preferences** → `/onboarding` (skills, experience, salary range, location)
3. **Swipe** → `/feed` — drag cards left/right or use arrow keys
4. **Match fires** → instant celebration modal with score breakdown
5. **View matches** → `/matches`
6. **Update profile** → `/profile` → auto-redirects back to feed

### Recruiter Flow
1. **Register company** → `/register/company`
2. **Post jobs** → `/jobs/new`
3. **Review matched candidates** → `/jobs/[id]/candidates`
4. **Update application status** → accept for interview / reject

---

## Seeded Companies & Jobs

The following companies and roles are pre-loaded for testing:

| Company | Role | Skills |
|---------|------|--------|
| Supastack Cloud | Senior Full-Stack Engineer | TypeScript, React, Next.js, Python, FastAPI, PostgreSQL |
| Supastack Cloud | Staff Distributed Systems Engineer | Go, Distributed Systems, PostgreSQL, Redis, Docker, Kubernetes |
| NeuralPath AI | AI Platform Engineer | Python, PyTorch, LLMs, pgvector, PostgreSQL, Docker, FastAPI |
| FinPulse Global | Senior Backend Architect | Python, FastAPI, PostgreSQL, Redis, Celery, Kafka, Docker |
| FinPulse Global | Frontend Engineer (Design Systems) | React, TypeScript, Tailwind CSS, Framer Motion, Next.js |
| Veloce Health | Full-Stack Software Engineer | TypeScript, React, Node.js, PostgreSQL, Docker |
| HyperScale Networks | DevOps & Infrastructure Engineer | Kubernetes, Docker, Terraform, AWS, CI/CD, Linux, Python |
| Prism Robotics | Computer Vision & ML Engineer | Python, PyTorch, OpenCV, Deep Learning, Linux, C++ |
| Aether Commerce | Principal Web Performance Engineer | Next.js, React, TypeScript, HTML5, CSS3, GraphQL |
| Chronos Analytics | Lead Data Platform Engineer | Python, Kafka, Redis, PostgreSQL, Docker, REST API |
| OpenForge Studio | Multiplayer Gameplay Engineer | C++, Python, Go, Git, REST API, Docker |
| Beacon Security | Application Security Engineer | Python, Linux, Docker, AWS, REST API, Git |
| Lumina Creative | Frontend Graphics Engineer | TypeScript, JavaScript, React, HTML5, CSS3, Framer Motion |
| Kite Logistics | Operations Systems Engineer | Python, FastAPI, PostgreSQL, Celery, Redis, TypeScript |
| Golang Gateway | Backend Engineer (Go) | Go, Docker, PostgreSQL, Redis |
| C-Sharp Innovations | .NET Developer | C#, .NET Core, SQL Server, Azure |

All company recruiter accounts use password: `Password123!`

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
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # matching_service, embedding_service, application_service
│   │   └── workers/         # Celery tasks (embedding generation, match recomputation)
│   ├── alembic/             # Database migrations
│   └── seed_data.py         # Company and job listing seed script
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   │   ├── (candidate)/     # Feed, matches, profile, onboarding
│   │   └── (company)/       # Dashboard, jobs, candidates
│   ├── components/          # SwipeDeck, SwipeCard, MatchScoreBreakdown, Navbar
│   ├── context/             # AuthContext (JWT decode, token refresh)
│   └── lib/                 # api-client.ts, types.ts
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
| `MATCH_SCORE_THRESHOLD` | `0.40` | Minimum score to trigger a match |
| `DAILY_SWIPE_CAP` | `50` | Max swipes per candidate per day |
