"""FastAPI dependency-injection providers.

These are used via ``Depends(...)`` in route signatures to obtain database
sessions, Redis clients, the current authenticated user, and application
settings.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated, Optional

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings, get_settings
from app.core.security import verify_token

# ---------------------------------------------------------------------------
# Engine & session factory (module-level singletons, created lazily)
# ---------------------------------------------------------------------------

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine(settings: Settings | None = None) -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = settings or get_settings()
        _engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            echo=settings.DEBUG,
            pool_pre_ping=True,
        )
    return _engine


def _get_session_factory(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        engine = _get_engine(settings)
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


# ---------------------------------------------------------------------------
# Database session dependency
# ---------------------------------------------------------------------------

async def get_db(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session, rolling back on error.

    Usage::

        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    factory = _get_session_factory(settings)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Redis dependency
# ---------------------------------------------------------------------------

_redis_client: Redis | None = None


async def get_redis(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Redis:
    """Return a shared ``redis.asyncio.Redis`` client instance.

    The client is created once and reused across requests (connection pooling
    is handled internally by *redis-py*).
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            retry_on_timeout=True,
        )
    return _redis_client


# ---------------------------------------------------------------------------
# Current-user dependencies
# ---------------------------------------------------------------------------

async def get_current_user(
    access_token: Annotated[str | None, Cookie(alias="access_token")] = None,
    db: AsyncSession = Depends(get_db),
):
    """Extract the JWT from the ``access_token`` cookie, validate it, and
    return the corresponding ``User`` ORM instance.

    Raises ``401`` if the token is missing, expired, or the user does not
    exist / is deactivated.
    """
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    try:
        payload = verify_token(access_token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
        )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim.",
        )

    # Late import to avoid circular dependency with models package.
    from app.models.user import User  # noqa: WPS433

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )
    return user


async def get_optional_user(
    access_token: Annotated[str | None, Cookie(alias="access_token")] = None,
    db: AsyncSession = Depends(get_db),
):
    """Same as ``get_current_user`` but returns ``None`` when no token is
    present instead of raising.  Useful for endpoints that behave differently
    for authenticated vs. anonymous visitors.
    """
    if access_token is None:
        return None

    try:
        payload = verify_token(access_token)
    except JWTError:
        return None

    user_id: str | None = payload.get("sub")
    if user_id is None:
        return None

    from app.models.user import User  # noqa: WPS433

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        return None
    return user
