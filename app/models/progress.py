"""UserProgress ORM model.

Tracks a user's advancement through courses and individual lessons,
including completion status, score, and time invested.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ProgressStatus(str, enum.Enum):
    """Tri-state progress indicator."""

    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"


class UserProgress(Base):
    """Per-user, per-course/lesson progress record."""

    __tablename__ = "user_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", "lesson_id", name="uq_user_course_lesson"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[ProgressStatus] = mapped_column(
        Enum(ProgressStatus, name="progress_status", create_constraint=True),
        nullable=False,
        default=ProgressStatus.not_started,
        server_default="not_started",
    )
    progress_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        server_default="0",
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_spent_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<UserProgress user={self.user_id} course={self.course_id} status={self.status.value}>"
