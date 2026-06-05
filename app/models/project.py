"""Project ORM model.

Standalone or course-linked coding projects with difficulty grading,
starter/solution code, and optional AI generation provenance.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Difficulty(str, enum.Enum):
    """Project difficulty tier."""

    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class Project(Base):
    """A self-contained coding project / assignment."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty, name="project_difficulty", create_constraint=True),
        nullable=False,
        default=Difficulty.beginner,
        server_default="beginner",
    )
    starter_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution_code: Mapped[str | None] = mapped_column(Text, nullable=True)

    requirements: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Project {self.title!r} difficulty={self.difficulty.value}>"
