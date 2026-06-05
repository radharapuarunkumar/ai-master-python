"""Resume ORM model.

Stores structured resume content (JSON), generated PDFs, and ATS
(Applicant Tracking System) analysis results.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Resume(TimestampMixin, Base):
    """A user-authored resume with optional AI-powered ATS analysis."""

    __tablename__ = "resumes"

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

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    template_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    ats_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ats_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    target_job_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    target_job_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    def __repr__(self) -> str:
        return f"<Resume {self.title!r} v{self.version} user={self.user_id}>"
