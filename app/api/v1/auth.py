"""
Authentication endpoints: Google OAuth callback, token refresh, logout, and current user.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, get_redis
from app.models.user import User
from app.schemas.auth import AuthResponse, FirebaseLoginRequest, GoogleCallbackRequest, UserResponse
from app.schemas.common import ResponseEnvelope
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Cookie settings
COOKIE_OPTS = dict(httponly=True, secure=True, samesite="strict")
ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


@router.post(
    "/google/callback",
    response_model=ResponseEnvelope[AuthResponse],
    status_code=status.HTTP_200_OK,
)
async def google_callback(
    body: GoogleCallbackRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ResponseEnvelope[AuthResponse]:
    """Exchange Google authorization code for JWT tokens.

    On success, sets httpOnly cookies and returns user profile + token metadata.
    """
    svc = AuthService(db=db, redis=redis)
    user, access_token, refresh_token = await svc.authenticate_google(
        code=body.code,
        redirect_uri=body.redirect_uri,
    )

    # Set secure httpOnly cookies
    response.set_cookie(ACCESS_COOKIE, access_token, max_age=900, **COOKIE_OPTS)
    response.set_cookie(REFRESH_COOKIE, refresh_token, max_age=604800, **COOKIE_OPTS)

    from app.config import get_settings
    settings = get_settings()

    return ResponseEnvelope(
        data=AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )
    )


@router.post(
    "/firebase/login",
    response_model=ResponseEnvelope[AuthResponse],
    status_code=status.HTTP_200_OK,
)
async def firebase_login(
    body: FirebaseLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ResponseEnvelope[AuthResponse]:
    """Verify a Firebase ID token issued by the frontend and start an app session.

    The frontend authenticates with Firebase (Google popup), then sends
    the resulting ID token here.  We verify it with Firebase Admin SDK,
    look up or create the user in the database, and set the same httpOnly
    JWT session cookies as the legacy Google OAuth flow.
    """
    svc = AuthService(db=db, redis=redis)
    user, access_token, refresh_token = await svc.authenticate_firebase(
        id_token=body.id_token,
    )

    response.set_cookie(ACCESS_COOKIE, access_token, max_age=900, **COOKIE_OPTS)
    response.set_cookie(REFRESH_COOKIE, refresh_token, max_age=604800, **COOKIE_OPTS)

    from app.config import get_settings
    settings = get_settings()

    return ResponseEnvelope(
        data=AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )
    )


@router.post(
    "/refresh",
    response_model=ResponseEnvelope[dict],
    status_code=status.HTTP_200_OK,
)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ResponseEnvelope[dict]:
    """Refresh the access token using the refresh token cookie.

    Implements refresh token rotation: old token is invalidated, new pair issued.
    """
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    svc = AuthService(db=db, redis=redis)
    new_access, new_refresh = await svc.refresh_tokens(refresh_token)

    response.set_cookie(ACCESS_COOKIE, new_access, max_age=900, **COOKIE_OPTS)
    response.set_cookie(REFRESH_COOKIE, new_refresh, max_age=604800, **COOKIE_OPTS)

    from app.config import get_settings
    settings = get_settings()

    return ResponseEnvelope(
        data={"expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60}
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    """Log out the current user by invalidating their refresh token."""
    refresh_token = request.cookies.get(REFRESH_COOKIE, "")
    svc = AuthService(db=db, redis=redis)
    await svc.logout(str(current_user.id), refresh_token)

    # Clear cookies
    response.delete_cookie(ACCESS_COOKIE)
    response.delete_cookie(REFRESH_COOKIE)

    return {"status": "success", "data": {"message": "Logged out successfully"}}


@router.get(
    "/me",
    response_model=ResponseEnvelope[UserResponse],
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[UserResponse]:
    """Return the authenticated user's profile."""
    return ResponseEnvelope(data=UserResponse.model_validate(current_user))
