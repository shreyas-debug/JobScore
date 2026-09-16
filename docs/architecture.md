# Architecture

## System Diagram

```
Browser (Next.js 14)
     │  HTTP / JSON
     ▼
FastAPI (Python 3.12)  ◄── JWT (role + tenant_id)
     │
     ├── PostgreSQL 16 (pgvector) ── RLS per tenant
     │        ├── candidates
     │        ├── companies + recruiters
     │        ├── job_listings  (vector column)
     │        ├── swipes
     │        ├── matches  (score + score_breakdown)
     │        └── applications
     │
     ├── Redis ───────────────────── Celery task queue
     │
     └── sentence-transformers (local) — all-MiniLM-L6-v2
```

## Key Design Decisions

### Monorepo with Route Groups

Single Next.js app with `(candidate)` and `(company)` route groups. Simpler to deploy and run for a portfolio project while keeping the two user journeys cleanly separated.

### Services Layer

Business logic lives in `app/services/`, not in route handlers. Routes are thin: parse request → call service → serialize response. This makes the matching logic testable without standing up an HTTP server.

### Multi-Tenancy via RLS

Every company-owned table has a `tenant_id` column and a Postgres Row-Level Security policy. `db/rls.py` sets `app.tenant_id` from the JWT claim at the start of each request. Even a forgotten `WHERE` clause can't leak across companies.

The DB user `jobscore` must NOT be a superuser — RLS is bypassed for superusers.

### Cursor-Based Pagination

`feed`, `matches`, and `candidate-feed` all use `?cursor=<base64-encoded-datetime>`. Offset pagination breaks when swipes are being written concurrently (rows shift, duplicate or skip entries).

### Idempotent Swipes

`POST /swipe` checks for an existing record before inserting. The unique constraint `(candidate_id, job_listing_id, swiped_by)` is the last line of defense. Returns `409 Conflict` on duplicate to make the behavior explicit and testable.

### Async Match Recomputation

Profile and listing edits trigger a Celery task instead of blocking the request. The task skips listings already swiped left — no zombie match resurrections.
