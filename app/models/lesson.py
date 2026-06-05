"""Lesson ORM model.

A ``Lesson`` belongs to a ``Module`` and represents a single learning unit
(reading, video, exercise, quiz, or project).
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class LessonType(str, enum.Enum):
    """The kind of learning activity a lesson represents."""

    reading = "reading"
    video = "video"
    exercise = "exercise"
    quiz = "quiz"
    project = "project"


class Lesson(TimestampMixin, Base):
    """A single lesson within a module."""

    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_html: Mapped[str | None] = mapped_column(Text, nullable=True)

    code_examples: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    exercise: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    lesson_type: Mapped[LessonType] = mapped_column(
        Enum(LessonType, name="lesson_type", create_constraint=True),
        nullable=False,
        default=LessonType.reading,
        server_default="reading",
    )
    video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    is_premium: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    def __repr__(self) -> str:
        return f"<Lesson {self.title!r} type={self.lesson_type.value}>"
