"""
SAMVAD API Security & Rate Limiting Middleware (Phase 4 — M4.3)

Provides:
- ApiKeyMiddleware: Token authentication via X-API-Key or Authorization Bearer header.
- RateLimiterMiddleware: Sliding-window in-memory rate limiter per client IP.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger("api.middleware")

# Endpoints exempt from API key and strict rate limiting
PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """
    Validates API key for non-public endpoints when settings.api_key is configured.
    Supports either 'X-API-Key: <key>' or 'Authorization: Bearer <key>'.
    """

    def __init__(self, app, settings: Optional[Settings] = None) -> None:
        super().__init__(app)
        self.settings = settings or get_settings()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Preflight OPTIONS requests always proceed (CORS)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Public endpoints bypass authentication
        path = request.url.path.rstrip("/") or "/"
        if path in PUBLIC_PATHS:
            return await call_next(request)

        expected_key = self.settings.api_key
        if not expected_key:
            # When no API key is configured, allow all traffic (dev mode)
            return await call_next(request)

        # Check X-API-Key header
        provided_key = request.headers.get("X-API-Key")
        if not provided_key:
            # Check Authorization: Bearer <token>
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                provided_key = auth_header[7:].strip()

        if not provided_key or provided_key != expected_key:
            logger.warning(
                "Unauthorized access attempt to %s from client %s",
                request.url.path,
                request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "detail": "Invalid or missing API key. Provide a valid key via 'X-API-Key' or 'Authorization: Bearer <key>'.",
                },
            )

        return await call_next(request)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    In-memory sliding window rate limiter per client IP address.
    Protects query and voice synthesis endpoints against exhaustion and denial-of-service.
    """

    def __init__(self, app, settings: Optional[Settings] = None) -> None:
        super().__init__(app)
        self.settings = settings or get_settings()
        # Storage: client_ip -> list of timestamps
        self._standard_requests: dict[str, list[float]] = defaultdict(list)
        self._voice_requests: dict[str, list[float]] = defaultdict(list)

    def _is_rate_limited(
        self,
        ip: str,
        bucket: dict[str, list[float]],
        limit: int,
        window_seconds: float = 60.0,
    ) -> bool:
        now = time.time()
        cutoff = now - window_seconds

        # Prune old timestamps
        history = [ts for ts in bucket[ip] if ts > cutoff]
        if len(history) >= limit:
            bucket[ip] = history
            return True

        history.append(now)
        bucket[ip] = history
        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.settings.enable_rate_limiting or request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path.rstrip("/")
        if path in PUBLIC_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        # Apply specific rate limit based on endpoint category
        if path.startswith("/api/v1/voice"):
            limit = self.settings.rate_limit_voice_per_minute
            bucket = self._voice_requests
        else:
            limit = self.settings.rate_limit_requests_per_minute
            bucket = self._standard_requests

        if self._is_rate_limited(client_ip, bucket, limit):
            logger.warning("Rate limit exceeded for client %s on %s", client_ip, path)
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": "60"},
                content={
                    "error": "Too Many Requests",
                    "detail": f"Rate limit of {limit} requests per minute exceeded. Please retry after 60 seconds.",
                },
            )

        return await call_next(request)

