"""
User-related Pydantic schemas.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.schemas.common import LevelEnum, RoleEnum


class UserUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None
    preferences: dict | None = None
    current_level: LevelEnum | None = None
    onboarding_completed: bool | None = None


class RoleUpdate(BaseModel):
    role: RoleEnum


class UserStats(BaseModel):
    courses_enrolled: int
    lessons_completed: int
    current_streak: int
    longest_streak: int
    total_time_minutes: int
    certificates_earned: int
    ai_chats_today: int
    ai_generations_today: int


class UserListItem(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    avatar_url: str | None
    role: RoleEnum
    current_level: LevelEnum
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserDetail(UserListItem):
    onboarding_completed: bool
    preferences: dict | None
    xp: int
    daily_streak: int
    interview_score: int
    resume_score: int
    project_score: int


class AdminUserUpdate(BaseModel):
    """Admin-only user update schema (can change any field)."""
    role: RoleEnum | None = None
    is_active: bool | None = None
    current_level: LevelEnum | None = None
