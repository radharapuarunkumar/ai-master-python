"""AIGeneration ORM model.

Logs every AI-generated artefact (explanations, code examples, quizzes,
study plans …) so users can review, rate, and bookmark them.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class GenerationType(str, enum.Enum):
    """Category of AI-generated content."""

    code_example = "code_example"
    explanation = "explanation"
    project_idea = "project_idea"
    problem_scenario = "problem_scenario"
    quiz = "quiz"
    flashcard = "flashcard"
    study_plan = "study_plan"


class AIGeneration(Base):
    """A single AI generation event and its result."""

    __tablename__ = "ai_generations"

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

    generation_type: Mapped[GenerationType] = mapped_column(
        Enum(GenerationType, name="generation_type", create_constraint=True),
        nullable=False,
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)

    rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    is_bookmarked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AIGeneration {self.generation_type.value} user={self.user_id}>"
