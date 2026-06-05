"""HTTP middleware stack: request-ID injection, response timing, and CORS.

Call ``setup_middleware(app)`` once during application startup to register
everything in the correct order.
"""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import get_settings


# ---------------------------------------------------------------------------
# Request-ID middleware
# ---------------------------------------------------------------------------

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Ensures every request/response carries an ``X-Request-ID`` header.

    If the client supplies one it is reused; otherwise a new UUID-4 is generated.
    The ID is also stored in ``request.state.request_id`` for downstream use
    (e.g. structured logging).
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# ---------------------------------------------------------------------------
# Timing middleware
# ---------------------------------------------------------------------------

class TimingMiddleware(BaseHTTPMiddleware):
    """Adds an ``X-Process-Time`` header (in seconds) to every response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        return response


# ---------------------------------------------------------------------------
# Setup helper
# ---------------------------------------------------------------------------

def setup_middleware(app: FastAPI) -> None:
    """Register all middleware on *app* in the recommended order.

    Middleware is evaluated **in reverse registration order** in Starlette,
    so we register from outermost to innermost:

    1. CORS (outermost — must handle pre-flight before anything else)
    2. RequestID
    3. Timing (innermost — measures actual handler time)
    """
    settings = get_settings()

    # 1. CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )

    # 2. Request-ID
    app.add_middleware(RequestIDMiddleware)

    # 3. Timing
    app.add_middleware(TimingMiddleware)
