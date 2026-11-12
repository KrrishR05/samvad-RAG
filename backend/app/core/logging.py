"""
SAMVAD Structured Logging & Request Correlation

Provides request-aware structured logging so that every log line
within a pipeline execution carries the associated request_id.
"""

from __future__ import annotations

import logging
import re
import sys
import uuid
from contextvars import ContextVar
from typing import Optional

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import get_settings

# Context variable for per-request tracing
current_request_id: ContextVar[Optional[str]] = ContextVar(
    "current_request_id", default=None
)

_SAFE_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def sanitize_request_id(candidate: Optional[str]) -> str:
    """Return a safe correlation ID or generate a fresh UUID4."""
    if candidate and _SAFE_REQUEST_ID_RE.match(candidate):
        return candidate
    return str(uuid.uuid4())


class RequestIdMiddleware:
    """Pure ASGI middleware binding per-request correlation ID to logging and response headers."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = MutableHeaders(scope=scope)
        rid = sanitize_request_id(headers.get("x-request-id"))
        state = scope.setdefault("state", {})
        state["request_id"] = rid

        token = current_request_id.set(rid)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                resp_headers = MutableHeaders(scope=message)
                resp_headers["X-Request-ID"] = rid
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            current_request_id.reset(token)


class RequestIdFilter(logging.Filter):
    """Inject the current request_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = current_request_id.get() or "-"  # type: ignore[attr-defined]
        return True


def setup_logging() -> None:
    """
    Configure the root logger with structured formatting.

    Log format includes timestamp, level, request_id, module, and message.
    Sensitive fields (API keys, secrets) must NEVER be logged.
    """
    settings = get_settings()

    log_format = (
        "%(asctime)s | %(levelname)-8s | "
        "req=%(request_id)s | %(name)s | %(message)s"
    )
    date_format = "%Y-%m-%dT%H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    root.handlers.clear()
    root.addHandler(handler)

    # Quiet noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger that inherits the structured formatter."""
    return logging.getLogger(name)
