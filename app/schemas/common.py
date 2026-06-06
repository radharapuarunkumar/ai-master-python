"""
Common/shared Pydantic schemas, enums, and response envelopes.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Enums (mirror SQLAlchemy model enums for API layer)
# ---------------------------------------------------------------------------

class RoleEnum(str, Enum):
    admin = "admin"
    premium = "premium"
    free = "free"


class LevelEnum(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class LessonTypeEnum(str, Enum):
    reading = "reading"
    video = "video"
    exercise = "exercise"
    quiz = "quiz"
    project = "project"


class ProgressStatusEnum(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"


class SessionTypeEnum(str, Enum):
    tutor = "tutor"
    interview = "interview"


class SessionStatusEnum(str, Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class InterviewTypeEnum(str, Enum):
    technical = "technical"
    hr = "hr"
    system_design = "system_design"
    placement = "placement"


class DifficultyEnum(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class GenerationTypeEnum(str, Enum):
    code_example = "code_example"
    explanation = "explanation"
    project_idea = "project_idea"
    problem_scenario = "problem_scenario"
    quiz = "quiz"
    flashcard = "flashcard"
    study_plan = "study_plan"


class MessageRoleEnum(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


# ---------------------------------------------------------------------------
# Generic response envelope
# ---------------------------------------------------------------------------

DataT = TypeVar("DataT")


class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class ResponseEnvelope(BaseModel, Generic[DataT]):
    """Standard success response wrapper used by all API endpoints."""
    status: str = "success"
    data: DataT
    meta: Optional[dict[str, Any]] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class ErrorResponse(BaseModel):
    status: str = "error"
    error: ErrorDetail


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    database: str
    redis: str
    status: str
