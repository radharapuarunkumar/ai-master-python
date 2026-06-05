"""JWT token creation, verification, and helper utilities.

Uses *python-jose* (``jose``) for compact JWS tokens with HMAC-SHA256.
Every token carries ``sub``, ``email``, ``role``, ``level``, ``exp``,
``iat``, and a unique ``jti`` to support revocation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import get_settings


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------

def create_access_token(data: dict, *, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived access JWT.

    Parameters
    ----------
    data:
        Claims to embed (typically ``sub``, ``email``, ``role``, ``level``).
    expires_delta:
        Custom expiry.  Falls back to ``ACCESS_TOKEN_EXPIRE_MINUTES``.

    Returns
    -------
    str
        Encoded JWT string.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    to_encode = {
        **data,
        "exp": expire,
        "iat": now,
        "jti": uuid.uuid4().hex,
        "type": "access",
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict, *, expires_delta: timedelta | None = None) -> str:
    """Create a long-lived refresh JWT.

    Parameters
    ----------
    data:
        Minimal claims (typically just ``sub``).
    expires_delta:
        Custom expiry.  Falls back to ``REFRESH_TOKEN_EXPIRE_DAYS``.

    Returns
    -------
    str
        Encoded JWT string.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))

    to_encode = {
        **data,
        "exp": expire,
        "iat": now,
        "jti": uuid.uuid4().hex,
        "type": "refresh",
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------

def verify_token(token: str) -> dict:
    """Decode and validate a JWT, returning the payload dict.

    Raises
    ------
    JWTError
        If the token is expired, tampered with, or otherwise invalid.
    """
    settings = get_settings()
    payload: dict = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require_exp": True, "require_iat": True},
    )
    # Ensure mandatory claims are present
    if "sub" not in payload:
        raise JWTError("Token missing 'sub' claim")
    return payload


# ---------------------------------------------------------------------------
# Convenience helper
# ---------------------------------------------------------------------------

def generate_token_pair(
    user_id: str,
    email: str,
    role: str,
    level: str,
) -> tuple[str, str]:
    """Return an ``(access_token, refresh_token)`` pair for the given user.

    This is the primary entry-point called after successful authentication.
    """
    common = {"sub": user_id, "email": email, "role": role, "level": level}
    access = create_access_token(common)
    refresh = create_refresh_token({"sub": user_id})
    return access, refresh
