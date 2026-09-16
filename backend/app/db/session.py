from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

import sys
from sqlalchemy.pool import NullPool

# Use NullPool for Celery workers because they create a new event loop per task with asyncio.run()
is_celery = "celery" in sys.argv[0] or "celery" in sys.argv

engine_kwargs = {
    "echo": settings.ENVIRONMENT == "development",
    "pool_pre_ping": True,
}

if is_celery:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionLocal() as session:
        yield session  # type: ignore[misc]
