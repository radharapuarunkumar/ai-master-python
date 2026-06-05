"""Application configuration using pydantic-settings.

All settings are loaded from environment variables with an optional `.env`
file fallback.  Secrets (API keys, DB credentials) should **never** be
committed — keep them in `.env` or a secrets manager.
"""

from __future__ import annotations

from functools import lru_cache
from typing import ClassVar

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised, validated application settings.

    Every attribute maps 1-to-1 to an environment variable of the same name
    (case-insensitive).  Pydantic validates types on startup so invalid
    configuration fails fast.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── General ───────────────────────────────────────────────────────────
    APP_NAME: str = "AI Master Python"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # ── Database (PostgreSQL + asyncpg) ───────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_master"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # ── Redis ─────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str | None = None

    # ── Google OAuth ──────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ── JWT ───────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE-ME-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Google Gemini AI ──────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    AI_PRO_MODEL: str = "gemini-2.5-pro"
    AI_FLASH_MODEL: str = "gemini-2.5-flash"
    AI_EMBEDDING_MODEL: str = "text-embedding-004"

    # ── LiveKit (real-time video) ─────────────────────────────────────────
    LIVEKIT_URL: str = ""
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""

    # ── Google Cloud Storage ──────────────────────────────────────────────
    GCS_BUCKET_NAME: str = ""
    GCS_CREDENTIALS_PATH: str | None = None

    # ── SendGrid (email) ──────────────────────────────────────────────────
    SENDGRID_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@aimasterpython.com"

    # ── CORS / Frontend ──────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Derived helpers (not from env) ────────────────────────────────────
    @property
    def cors_origins(self) -> list[str]:
        """Return the list of allowed CORS origins."""
        origins = [self.FRONTEND_URL]
        if self.DEBUG:
            origins.extend(["http://localhost:3000", "http://localhost:5173"])
        return list(set(origins))

    @field_validator("DATABASE_URL")
    @classmethod
    def _validate_database_url(cls, v: str) -> str:
        if not v.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://")):
            raise ValueError(
                "DATABASE_URL must use the 'postgresql+asyncpg://' or "
                "'sqlite+aiosqlite://' scheme for async support."
            )
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()  # type: ignore[call-arg]
