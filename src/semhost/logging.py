from __future__ import annotations

import contextvars
import json
import logging
import sys
import time
import uuid
from typing import Any, Dict, Iterable


_ctx_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


def set_request_id(value: str | None) -> None:
    _ctx_request_id.set(value)


def get_request_id() -> str | None:
    return _ctx_request_id.get()


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        rid = get_request_id()
        if rid is not None:
            setattr(record, "request_id", rid)
        return True


class JsonFormatter(logging.Formatter):
    DEFAULT_EXCLUDE: set[str] = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: Dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
            + f".{int((record.created - int(record.created)) * 1000):03d}Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }
        rid = getattr(record, "request_id", None)
        if rid is not None:
            payload["request_id"] = rid
        # Include extras (e.g., session_id, round_index)
        for k, v in record.__dict__.items():
            if k not in self.DEFAULT_EXCLUDE and k not in payload:
                # Avoid non-serializable by best-effort repr
                try:
                    json.dumps(v)
                    payload[k] = v
                except Exception:
                    payload[k] = repr(v)
        return json.dumps(payload, separators=(",", ":"))


def setup_logging(level: str = "INFO", json_enabled: bool = True) -> None:
    logger = logging.getLogger("semhost")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(ContextFilter())
    if json_enabled:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(handler)


def get_logger() -> logging.Logger:
    return logging.getLogger("semhost")


class RequestContextMiddleware:
    """ASGI middleware to inject request_id and emit minimal access logs.

    - Uses X-Request-Id if provided; otherwise generates a short UUID.
    - Handles both HTTP and WebSocket scopes.
    """

    def __init__(self, app):  # type: ignore[no-untyped-def]
        self.app = app

    async def __call__(self, scope, receive, send):  # type: ignore[no-untyped-def]
        scope_type = scope.get("type")
        headers: Iterable[tuple[bytes, bytes]] = scope.get("headers", [])
        req_id = None
        for k, v in headers:
            if k.lower() == b"x-request-id":
                try:
                    req_id = v.decode("utf-8").strip() or None
                except Exception:
                    req_id = None
                break
        if req_id is None:
            req_id = str(uuid.uuid4())[:8]
        token = _ctx_request_id.set(req_id)
        try:
            lg = get_logger()
            path = scope.get("path", "?")
            lg.info("request", extra={"path": path, "scope": scope_type})
            await self.app(scope, receive, send)
        finally:
            _ctx_request_id.reset(token)

