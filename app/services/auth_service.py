"""
Authentication service: Google OAuth flow, JWT issuance, token refresh, logout.
"""
from __future__ import annotations

import json
import logging
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import generate_token_pair, verify_token
from app.integrations.google_oauth import GoogleOAuthClient
from app.models.user import User, Level, Role

logger = logging.getLogger(__name__)
settings = get_settings()

# Redis key prefix for refresh token allowlist
REFRESH_TOKEN_PREFIX = "refresh_token:"
REFRESH_TOKEN_TTL = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400  # seconds


class AuthService:
    """Handles all authentication and session management logic."""

    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self.db = db
        self.redis = redis
        self.oauth = GoogleOAuthClient(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )

    async def authenticate_google(
        self, code: str, redirect_uri: str | None = None
    ) -> tuple[User, str, str]:
        """Full Google OAuth flow: exchange code → fetch user → issue JWTs.

        Args:
            code: Authorization code from Google redirect.
            redirect_uri: Optional override redirect URI.

        Returns:
            Tuple of (user, access_token, refresh_token).

        Raises:
            UnauthorizedError: If Google rejects the code or token.
        """
        try:
            tokens = await self.oauth.exchange_code(code, redirect_uri)
        except ValueError as e:
            raise UnauthorizedError(str(e)) from e

        try:
            google_user = await self.oauth.get_user_info(tokens["access_token"])
        except ValueError as e:
            raise UnauthorizedError(str(e)) from e

        user = await self._get_or_create_user(google_user)

        access_token, refresh_token = generate_token_pair(
            user_id=str(user.id),
            email=user.email,
            role=user.role.value,
            level=user.current_level.value,
        )

        # Store refresh token in Redis allowlist
        await self._store_refresh_token(str(user.id), refresh_token)

        # Update last login
        from sqlalchemy import func
        user.last_login_at = func.now()
        await self.db.commit()
        await self.db.refresh(user)

        logger.info("User authenticated via Google", extra={"user_id": str(user.id)})
        return user, access_token, refresh_token

    async def authenticate_firebase(self, id_token: str) -> tuple[User, str, str]:
        """Verify a Firebase ID token and issue app JWT tokens.

        This is the new primary auth path — the frontend authenticates with
        Firebase (Google popup) and sends the resulting ID token here.

        Args:
            id_token: Firebase ID token from the client.

        Returns:
            Tuple of (user, access_token, refresh_token).

        Raises:
            UnauthorizedError: If the Firebase token is invalid or expired.
        """
        from app.integrations.firebase_admin import verify_firebase_token

        try:
            firebase_user = await verify_firebase_token(id_token)
        except ValueError as exc:
            raise UnauthorizedError(str(exc)) from exc

        # Map Firebase claims → same dict shape as _get_or_create_user expects
        google_user = {
            "id":      firebase_user["firebase_uid"],
            "email":   firebase_user["email"],
            "name":    firebase_user["name"],
            "picture": firebase_user["picture"],
        }

        user = await self._get_or_create_user(google_user)

        access_token, refresh_token = generate_token_pair(
            user_id=str(user.id),
            email=user.email,
            role=user.role.value,
            level=user.current_level.value,
        )

        await self._store_refresh_token(str(user.id), refresh_token)

        from sqlalchemy import func
        user.last_login_at = func.now()
        await self.db.commit()
        await self.db.refresh(user)

        logger.info("User authenticated via Firebase", extra={"user_id": str(user.id)})
        return user, access_token, refresh_token

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        """Validate refresh token and issue a new token pair.

        Args:
            refresh_token: The refresh JWT from the client cookie.

        Returns:
            New (access_token, refresh_token) pair.

        Raises:
            UnauthorizedError: If token is invalid, expired, or not in allowlist.
        """
        try:
            payload = verify_token(refresh_token, expected_type="refresh")
        except Exception as e:
            raise UnauthorizedError("Invalid refresh token") from e

        user_id: str = payload["sub"]

        # Check allowlist in Redis
        stored = await self.redis.get(f"{REFRESH_TOKEN_PREFIX}{user_id}:{refresh_token[:16]}")
        if not stored:
            raise UnauthorizedError("Refresh token has been revoked or expired")

        # Load current user (role/level might have changed)
        result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise UnauthorizedError("User account not found or deactivated")

        # Revoke old refresh token
        await self.redis.delete(f"{REFRESH_TOKEN_PREFIX}{user_id}:{refresh_token[:16]}")

        # Issue new pair
        new_access, new_refresh = generate_token_pair(
            user_id=str(user.id),
            email=user.email,
            role=user.role.value,
            level=user.current_level.value,
        )
        await self._store_refresh_token(user_id, new_refresh)

        return new_access, new_refresh

    async def logout(self, user_id: str, refresh_token: str) -> None:
        """Revoke the refresh token, effectively logging the user out.

        Args:
            user_id: The authenticated user's ID.
            refresh_token: The refresh JWT to invalidate.
        """
        key = f"{REFRESH_TOKEN_PREFIX}{user_id}:{refresh_token[:16]}"
        await self.redis.delete(key)
        logger.info("User logged out", extra={"user_id": user_id})

    async def logout_all(self, user_id: str) -> None:
        """Revoke ALL refresh tokens for a user (admin action or account security)."""
        pattern = f"{REFRESH_TOKEN_PREFIX}{user_id}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_or_create_user(self, google_user: dict) -> User:
        """Find an existing user by Google ID or create a new free account.

        Args:
            google_user: Profile dict from Google's userinfo endpoint.

        Returns:
            The existing or newly created User ORM object.
        """
        google_id = str(google_user["id"])
        email = google_user["email"]

        # Try to find by google_id first (most common path)
        result = await self.db.execute(
            select(User).where(User.google_id == google_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            # Fallback: find by email (user might have signed up differently)
            result = await self.db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()

        if user is None:
            # New user — create free account
            user = User(
                email=email,
                full_name=google_user.get("name", email.split("@")[0]),
                avatar_url=google_user.get("picture"),
                google_id=google_id,
                role=Role.free,
                current_level=Level.beginner,
            )
            self.db.add(user)
            await self.db.flush()  # Get the generated UUID
            logger.info("New user created", extra={"email": email})
        else:
            # Existing user — update profile picture if changed
            if google_user.get("picture") and user.avatar_url != google_user["picture"]:
                user.avatar_url = google_user["picture"]
            if not user.google_id:
                user.google_id = google_id

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def _store_refresh_token(self, user_id: str, refresh_token: str) -> None:
        """Store a refresh token in Redis allowlist with TTL."""
        key = f"{REFRESH_TOKEN_PREFIX}{user_id}:{refresh_token[:16]}"
        await self.redis.setex(key, REFRESH_TOKEN_TTL, "1")
