"""User ORM model.

Stores authentication details (Google OAuth ``google_id``), profile data,
role/level state, and user preferences.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Role(str, enum.Enum):
    """User privilege role."""

    admin = "admin"
    premium = "premium"
    free = "free"


class Level(str, enum.Enum):
    """Current learning level."""

    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class User(TimestampMixin, Base):
    """Core user account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    role: Mapped[Role] = mapped_column(
        Enum(Role, name="user_role", create_constraint=True),
        nullable=False,
        default=Role.free,
        server_default="free",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    current_level: Mapped[Level] = mapped_column(
        Enum(Level, name="user_level", create_constraint=True),
        nullable=False,
        default=Level.beginner,
        server_default="beginner",
    )
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    preferences: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    xp: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    daily_streak: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    attendance_log: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    interview_score: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    resume_score: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    project_score: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)

    def __repr__(self) -> str:
        return f"<User {self.email!r} role={self.role.value}>"
