from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import FastAPI
from starlette.responses import JSONResponse


@dataclass
class DomainError(Exception):
    status_code: int
    detail: str
    code: Optional[str] = None  # internal error code (not exposed yet)


class BadRequestError(DomainError):
    def __init__(self, detail: str = "bad request", code: Optional[str] = None) -> None:
        super().__init__(400, detail, code)


class UnauthorizedError(DomainError):
    def __init__(self, detail: str = "unauthorized", code: Optional[str] = None) -> None:
        super().__init__(401, detail, code)


class ForbiddenError(DomainError):
    def __init__(self, detail: str = "forbidden", code: Optional[str] = None) -> None:
        super().__init__(403, detail, code)


class NotFoundError(DomainError):
    def __init__(self, detail: str = "not found", code: Optional[str] = None) -> None:
        super().__init__(404, detail, code)


class ConflictError(DomainError):
    def __init__(self, detail: str = "conflict", code: Optional[str] = None) -> None:
        super().__init__(409, detail, code)


class RateLimitError(DomainError):
    def __init__(self, detail: str = "too many requests", code: Optional[str] = None) -> None:
        super().__init__(429, detail, code)


class ServiceUnavailableError(DomainError):
    def __init__(self, detail: str = "service unavailable", code: Optional[str] = None) -> None:
        super().__init__(503, detail, code)


def _domain_error_handler(_req, exc: DomainError):  # type: ignore[no-untyped-def]
    # Preserve backward compatibility: respond with the standard {"detail": ...}
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _domain_error_handler)

