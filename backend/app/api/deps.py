from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import InvalidTokenError, decode_token
from app.db.rls import set_tenant
from app.db.session import get_session

bearer = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Decode the JWT and return the payload dict.

    Also sets the Postgres RLS session variable if a tenant_id is present.
    """
    try:
        payload = decode_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise UnauthorizedError(str(exc)) from exc

    if tenant_id := payload.get("tenant_id"):
        await set_tenant(db, str(tenant_id))

    return payload


def require_role(*roles: str):
    """Dependency factory — raises 403 if the token's role isn't in `roles`."""

    async def _check(payload: Annotated[dict, Depends(get_current_user)]) -> dict:
        if payload.get("role") not in roles:
            raise ForbiddenError(
                f"This endpoint requires one of these roles: {', '.join(roles)}. "
                f"Your token has role={payload.get('role')!r}."
            )
        return payload

    return _check


def get_current_candidate(payload: Annotated[dict, Depends(get_current_user)]) -> dict:
    if payload.get("role") != "candidate":
        raise ForbiddenError("Candidate access only.")
    return payload


def get_current_recruiter(payload: Annotated[dict, Depends(get_current_user)]) -> dict:
    if payload.get("role") not in ("recruiter", "owner"):
        raise ForbiddenError("Recruiter or owner access only.")
    return payload
