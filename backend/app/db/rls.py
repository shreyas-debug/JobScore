from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_tenant(session: AsyncSession, tenant_id: str) -> None:
    """Set the Postgres session variable used by RLS policies.

    Must be called at the start of every request that touches tenant-scoped tables.
    The JWT claim value is passed in verbatim so the policy can compare:
        current_setting('app.tenant_id')::uuid = tenant_id
    """
    await session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": tenant_id})
