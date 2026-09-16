from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application error — always renders as structured JSON."""

    code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404


class UnauthorizedError(AppError):
    code = "UNAUTHORIZED"
    status_code = 401


class ForbiddenError(AppError):
    code = "FORBIDDEN"
    status_code = 403


class ConflictError(AppError):
    code = "CONFLICT"
    status_code = 409


class RateLimitError(AppError):
    code = "RATE_LIMITED"
    status_code = 429

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class TenantMismatchError(AppError):
    code = "TENANT_MISMATCH"
    status_code = 403


class ValidationAppError(AppError):
    code = "VALIDATION_ERROR"
    status_code = 422


def _error_response(exc: AppError) -> JSONResponse:
    headers = {}
    if isinstance(exc, RateLimitError) and exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "field": exc.field}},
        headers=headers,
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:  # noqa: ARG001
    return _error_response(exc)


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred.", "field": None}},
    )
