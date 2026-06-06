"""
AI Master Python — FastAPI application entry point.

Configures the app, registers middleware, exception handlers,
and all API routers. Manages startup/shutdown lifecycle events.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware, TimingMiddleware

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Lifespan: startup + shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialise resources on startup, clean up on shutdown."""
    setup_logging()
    logger.info(
        "Starting %s (debug=%s)", settings.APP_NAME, settings.DEBUG
    )

    # Initialise SQLAlchemy async engine
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        echo=settings.DEBUG,
        future=True,
    )
    app.state.db_engine = engine
    app.state.SessionLocal = async_sessionmaker(
        engine, expire_on_commit=False
    )

    # Initialise Redis
    from redis.asyncio import from_url
    redis = from_url(
        settings.REDIS_URL,
        password=settings.REDIS_PASSWORD or None,
        decode_responses=True,
    )
    app.state.redis = redis

    # Verify Redis connection
    try:
        await redis.ping()
        logger.info("Redis connection established")
    except Exception as exc:
        logger.warning("Redis unavailable at startup: %s", exc)

    # Firebase Admin SDK — verify service account is configured
    from app.integrations.firebase_admin import startup_check as firebase_startup_check
    firebase_startup_check()

    logger.info("%s started successfully", settings.APP_NAME)
    yield

    # Shutdown
    logger.info("Shutting down %s", settings.APP_NAME)
    await redis.aclose()
    await engine.dispose()
    logger.info("Resources cleaned up")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "AI-powered Python learning platform with live AI tutoring, "
            "interview simulation, career tools, and beta AI generation features."
        ),
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # Middleware (order matters: outermost first)
    # ------------------------------------------------------------------
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Exception handlers
    # ------------------------------------------------------------------
    register_exception_handlers(app)

    # ------------------------------------------------------------------
    # API Routers (v1)
    # ------------------------------------------------------------------
    from app.api.v1.auth import router as auth_router
    from app.api.v1.certificates import router as certificates_router
    from app.api.v1.chat import router as chat_router
    from app.api.v1.courses import router as courses_router
    from app.api.v1.interviews import router as interviews_router
    from app.api.v1.progress import router as progress_router
    from app.api.v1.projects import router as projects_router
    from app.api.v1.resumes import router as resumes_router
    from app.api.v1.users import router as users_router
    from app.api.v1.jobs import router as jobs_router
    from app.api.v1.community import router as community_router

    PREFIX = settings.API_V1_PREFIX

    # Add each router
    app.include_router(auth_router, prefix=PREFIX)
    app.include_router(users_router, prefix=PREFIX)
    app.include_router(courses_router, prefix=PREFIX)
    app.include_router(progress_router, prefix=PREFIX)
    app.include_router(projects_router, prefix=PREFIX)
    app.include_router(chat_router, prefix=PREFIX)
    app.include_router(interviews_router, prefix=PREFIX)
    app.include_router(resumes_router, prefix=PREFIX)
    app.include_router(certificates_router, prefix=PREFIX)
    app.include_router(jobs_router, prefix=PREFIX)
    app.include_router(community_router, prefix=PREFIX)

    # ------------------------------------------------------------------
    # Health check endpoints
    # ------------------------------------------------------------------

    @app.get("/", tags=["Root"], include_in_schema=False)
    async def root():
        """Root endpoint returning app status."""
        return {"status": "ok", "app": "AI Master Python"}

    @app.get("/health", tags=["Health"], include_in_schema=False)
    async def health():
        """Basic liveness check — always returns 200 if the app is running."""
        return {"status": "healthy"}

    @app.get("/health/live", tags=["Health"], include_in_schema=False)
    async def liveness():
        """Kubernetes liveness probe."""
        return JSONResponse(content={"status": "ok"})

    @app.get("/health/ready", tags=["Health"], include_in_schema=False)
    async def readiness():
        """Readiness probe: checks DB and Redis connectivity."""
        checks: dict[str, str] = {}
        overall = "healthy"

        # Database check
        try:
            from sqlalchemy import text
            async with app.state.SessionLocal() as session:
                await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as exc:
            checks["database"] = f"error: {exc}"
            overall = "degraded"

        # Redis check
        try:
            await app.state.redis.ping()
            checks["redis"] = "ok"
        except Exception as exc:
            checks["redis"] = f"error: {exc}"
            overall = "degraded"

        status_code = 200 if overall == "healthy" else 503
        return JSONResponse(
            content={"status": overall, **checks},
            status_code=status_code,
        )

    return app


# ---------------------------------------------------------------------------
# Application instance (used by uvicorn)
# ---------------------------------------------------------------------------
app = create_app()
