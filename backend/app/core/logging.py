"""
SAMVAD Structured Logging

Provides request-aware structured logging so that every log line
within a pipeline execution carries the associated request_id.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Optional

from app.core.config import get_settings

# Context variable for per-request tracing
current_request_id: ContextVar[Optional[str]] = ContextVar(
    "current_request_id", default=None
)


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
