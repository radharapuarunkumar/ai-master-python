"""Video, interview session, and interview question ORM models.

``VideoSession`` covers both live-tutor and mock-interview sessions.
``InterviewSession`` and ``InterviewQuestion`` add interview-specific
scoring and AI evaluation data.
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
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SessionType(str, enum.Enum):
    """Kind of video session."""

    tutor = "tutor"
    interview = "interview"


class VideoSessionStatus(str, enum.Enum):
    """Lifecycle status of a video session."""

    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class InterviewType(str, enum.Enum):
    """Category of mock interview."""

    behavioral = "behavioral"
    technical = "technical"
    system_design = "system_design"
    coding = "coding"


class InterviewDifficulty(str, enum.Enum):
    """Difficulty level for interview sessions."""

    easy = "easy"
    medium = "medium"
    hard = "hard"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class VideoSession(Base):
    """A real-time video session (tutoring or interview)."""

    __tablename__ = "video_sessions"

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
    session_type: Mapped[SessionType] = mapped_column(
        Enum(SessionType, name="video_session_type", create_constraint=True),
        nullable=False,
    )
    status: Mapped[VideoSessionStatus] = mapped_column(
        Enum(VideoSessionStatus, name="video_session_status", create_constraint=True),
        nullable=False,
        default=VideoSessionStatus.scheduled,
        server_default="scheduled",
    )

    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    livekit_room_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    recording_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    topic: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────
    interview: Mapped["InterviewSession | None"] = relationship(
        "InterviewSession",
        back_populates="video_session",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<VideoSession {self.id} type={self.session_type.value}>"


class InterviewSession(Base):
    """Interview-specific scoring and feedback, linked 1-to-1 to a VideoSession."""

    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    video_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("video_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    interview_type: Mapped[InterviewType] = mapped_column(
        Enum(InterviewType, name="interview_type", create_constraint=True),
        nullable=False,
    )
    difficulty: Mapped[InterviewDifficulty] = mapped_column(
        Enum(InterviewDifficulty, name="interview_difficulty", create_constraint=True),
        nullable=False,
        default=InterviewDifficulty.medium,
        server_default="medium",
    )

    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    strengths: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    improvements: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────
    video_session: Mapped["VideoSession"] = relationship(
        "VideoSession",
        back_populates="interview",
    )
    questions: Mapped[list["InterviewQuestion"]] = relationship(
        "InterviewQuestion",
        back_populates="interview",
        cascade="all, delete-orphan",
        order_by="InterviewQuestion.order_index",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<InterviewSession {self.id} type={self.interview_type.value}>"


class InterviewQuestion(Base):
    """An individual question asked during a mock interview."""

    __tablename__ = "interview_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_answer: Mapped[str | None] = mapped_column(Text, nullable=True)

    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_evaluation: Mapped[str | None] = mapped_column(Text, nullable=True)

    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    asked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Relationships ─────────────────────────────────────────────────────
    interview: Mapped["InterviewSession"] = relationship(
        "InterviewSession",
        back_populates="questions",
    )

    def __repr__(self) -> str:
        return f"<InterviewQuestion {self.id} order={self.order_index}>"
