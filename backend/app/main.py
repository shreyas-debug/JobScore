from __future__ import annotations

import logging
import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import AppError, app_error_handler, generic_error_handler
from app.api.v1.auth import router as auth_router
from app.api.v1.candidate.profile import router as candidate_profile_router
from app.api.v1.candidate.feed import router as candidate_feed_router
from app.api.v1.candidate.swipe import router as candidate_swipe_router
from app.api.v1.company.jobs import router as company_jobs_router
from app.api.v1.company.candidate_feed import router as company_applications_router
from app.api.v1.company.dashboard import router as company_dashboard_router

# ── Structured logging ────────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Jobscore API",
        version="1.0.0",
        description="Explainable swipe-based job matching platform",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request ID middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # ── Exception handlers ────────────────────────────────────────────────
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_error_handler)

    # ── Routers ───────────────────────────────────────────────────────────
    PREFIX = "/api/v1"
    app.include_router(auth_router, prefix=PREFIX)
    app.include_router(candidate_profile_router, prefix=PREFIX)
    app.include_router(candidate_feed_router, prefix=PREFIX)
    app.include_router(candidate_swipe_router, prefix=PREFIX)
    app.include_router(company_jobs_router, prefix=PREFIX)
    app.include_router(company_applications_router, prefix=PREFIX)
    app.include_router(company_dashboard_router, prefix=PREFIX)

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok", "environment": settings.ENVIRONMENT}

    return app


app = create_app()
