"""
Auth-related Pydantic schemas.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.schemas.common import LevelEnum, RoleEnum


class GoogleCallbackRequest(BaseModel):
    code: str
    redirect_uri: str | None = None


class FirebaseLoginRequest(BaseModel):
    """Request body for POST /auth/firebase/login.

    The frontend signs in via Firebase (Google popup), then sends the resulting
    Firebase ID token to this endpoint to establish a backend session.
    """
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str | None = None  # also accepted from cookie


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    avatar_url: str | None
    role: RoleEnum
    current_level: LevelEnum
    onboarding_completed: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Combined auth response: tokens + user profile."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
