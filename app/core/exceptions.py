"""Custom exception hierarchy and FastAPI exception handlers.

All API errors are returned as a uniform JSON envelope::

    {
        "status": "error",
        "error": {
            "code": "NOT_FOUND",
            "message": "Course not found."
        }
    }
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


# ---------------------------------------------------------------------------
# Base exception
# ---------------------------------------------------------------------------

class AppError(Exception):
    """Base class for all application-domain errors."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, *, details: Any = None) -> None:
        self.message = message or self.__class__.message
        self.details = details
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Concrete exceptions
# ---------------------------------------------------------------------------

class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"
    message = "The requested resource was not found."


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"
    message = "You do not have permission to perform this action."


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"
    message = "Authentication is required."


class BadRequestError(AppError):
    status_code = 400
    code = "BAD_REQUEST"
    message = "The request was invalid."


class RateLimitError(AppError):
    status_code = 429
    code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests. Please try again later."


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"
    message = "The request conflicts with the current state of the resource."


# ---------------------------------------------------------------------------
# JSON envelope builder
# ---------------------------------------------------------------------------

def _error_response(status_code: int, code: str, message: str, details: Any = None) -> JSONResponse:
    body: dict[str, Any] = {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def _handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
    return _error_response(exc.status_code, exc.code, exc.message, exc.details)


async def _handle_http_exception(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(exc.status_code, "HTTP_ERROR", str(exc.detail))


async def _handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
        details=exc.errors(),
    )


async def _handle_generic_error(_request: Request, exc: Exception) -> JSONResponse:
    # In production you would log the traceback here; never expose internals.
    return _error_response(500, "INTERNAL_ERROR", "An unexpected error occurred.")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_exception_handlers(app: FastAPI) -> None:
    """Attach all custom exception handlers to the FastAPI application."""
    app.add_exception_handler(AppError, _handle_app_error)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_generic_error)  # type: ignore[arg-type]
