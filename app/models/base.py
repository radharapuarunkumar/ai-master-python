"""SQLAlchemy declarative base and shared mixins.

All ORM models should inherit from ``Base`` and optionally mix in
``TimestampMixin`` for automatic ``created_at`` / ``updated_at`` columns.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    """Application-wide declarative base.

    Provides ``type_annotation_map`` so that common Python types are mapped
    to the preferred PostgreSQL column types automatically.
    """

    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
        datetime: DateTime(timezone=True),
    }


class TimestampMixin:
    """Mixin that adds ``created_at`` and ``updated_at`` columns.

    ``created_at`` is set once by the database on INSERT.
    ``updated_at`` is refreshed on every UPDATE.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
