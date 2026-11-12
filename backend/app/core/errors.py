"""
SAMVAD Error Handling

Centralized custom exceptions and FastAPI exception handlers.
All API errors return a consistent JSON envelope.
Stack traces are never exposed to the client.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.logging import current_request_id

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class SamvadError(Exception):
    """Base exception for all SAMVAD errors."""

    def __init__(
        self,
        message: str = "An internal error occurred.",
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        request_id: Optional[str] = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.request_id = request_id
        super().__init__(self.message)


class SpeechProcessingError(SamvadError):
    """Raised when STT processing fails."""

    def __init__(
        self,
        message: str = "Speech processing failed.",
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code="SPEECH_PROCESSING_ERROR",
            status_code=502,
            request_id=request_id,
        )


class RetrievalError(SamvadError):
    """Raised when the retrieval pipeline fails."""

    def __init__(
        self,
        message: str = "Unable to retrieve relevant context.",
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code="RETRIEVAL_ERROR",
            status_code=500,
            request_id=request_id,
        )


class GenerationError(SamvadError):
    """Raised when answer generation fails."""

    def __init__(
        self,
        message: str = "Answer generation failed.",
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code="GENERATION_ERROR",
            status_code=500,
            request_id=request_id,
        )


class GuardrailError(SamvadError):
    """Raised when a guardrail check fails."""

    def __init__(
        self,
        message: str = "Guardrail check failed.",
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code="GUARDRAIL_ERROR",
            status_code=422,
            request_id=request_id,
        )


class ConfigurationError(SamvadError):
    """Raised when required configuration is missing or invalid."""

    def __init__(
        self,
        message: str = "Service configuration error.",
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            status_code=500,
            request_id=request_id,
        )


class PipelineTimeoutError(SamvadError):
    """Raised when the pipeline exceeds its timeout."""

    def __init__(
        self,
        message: str = "Pipeline execution timed out.",
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code="PIPELINE_TIMEOUT",
            status_code=504,
            request_id=request_id,
        )


class InputValidationError(SamvadError):
    """Raised on invalid user input (empty audio, bad format, etc.)."""

    def __init__(
        self,
        message: str = "Invalid input provided.",
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code="INPUT_VALIDATION_ERROR",
            status_code=400,
            request_id=request_id,
        )


class PayloadTooLargeError(SamvadError):
    """Raised when an uploaded payload exceeds configured size limits."""

    def __init__(
        self,
        message: str = "Uploaded payload exceeds maximum allowed size.",
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code="PAYLOAD_TOO_LARGE",
            status_code=413,
            request_id=request_id,
        )


# ---------------------------------------------------------------------------
# Error response builder
# ---------------------------------------------------------------------------

def _build_error_body(
    code: str,
    message: str,
    request_id: Optional[str] = None,
) -> dict:
    body: dict = {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
        },
    }
    if request_id:
        body["request_id"] = request_id
    return body


def _resolve_request_id(request: Request, explicit: Optional[str] = None) -> Optional[str]:
    return (
        explicit
        or getattr(request.state, "request_id", None)
        or current_request_id.get()
    )


# ---------------------------------------------------------------------------
# FastAPI exception handlers
# ---------------------------------------------------------------------------

def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI application."""

    @app.exception_handler(SamvadError)
    async def samvad_error_handler(
        request: Request, exc: SamvadError
    ) -> JSONResponse:
        rid = _resolve_request_id(request, exc.request_id)
        logger.error(
            "SamvadError [%s]: %s (request_id=%s)",
            exc.code,
            exc.message,
            rid,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_body(
                code=exc.code,
                message=exc.message,
                request_id=rid,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        rid = _resolve_request_id(request)
        logger.exception("Unhandled exception (request_id=%s): %s", rid, exc)
        return JSONResponse(
            status_code=500,
            content=_build_error_body(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred.",
                request_id=rid,
            ),
        )
