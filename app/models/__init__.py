"""Model package — imports every ORM model for Alembic autodiscovery.

Alembic's ``env.py`` should set ``target_metadata = Base.metadata`` after
importing this package so that ``autogenerate`` picks up all tables.
"""

from app.models.base import Base, TimestampMixin  # noqa: F401

# Domain models
from app.models.user import User  # noqa: F401
from app.models.course import Course, Module  # noqa: F401
from app.models.lesson import Lesson  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.progress import UserProgress  # noqa: F401
from app.models.certificate import Certificate  # noqa: F401
from app.models.chat import ChatSession, ChatMessage  # noqa: F401
from app.models.video_session import (  # noqa: F401
    VideoSession,
    InterviewSession,
    InterviewQuestion,
)
from app.models.resume import Resume  # noqa: F401
from app.models.ai_generation import AIGeneration  # noqa: F401
from app.models.admin import PlatformSettings, AuditLog  # noqa: F401

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "Course",
    "Module",
    "Lesson",
    "Project",
    "UserProgress",
    "Certificate",
    "ChatSession",
    "ChatMessage",
    "VideoSession",
    "InterviewSession",
    "InterviewQuestion",
    "Resume",
    "AIGeneration",
    "PlatformSettings",
    "AuditLog",
]
