from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "jobscore",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,  # Acknowledge after task completes (safer for idempotency)
    worker_prefetch_multiplier=1,
)
