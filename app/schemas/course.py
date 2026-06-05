"""
Course, Module, and Lesson Pydantic schemas.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import LessonTypeEnum, LevelEnum


# ---------------------------------------------------------------------------
# Lesson schemas
# ---------------------------------------------------------------------------

class LessonCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content_markdown: str
    content_html: str | None = None
    code_examples: list[dict] | None = None
    exercise: dict | None = None
    lesson_type: LessonTypeEnum = LessonTypeEnum.reading
    video_url: str | None = None
    estimated_minutes: int | None = None
    order_index: int = 0
    is_premium: bool = False


class LessonUpdate(BaseModel):
    title: str | None = None
    content_markdown: str | None = None
    content_html: str | None = None
    code_examples: list[dict] | None = None
    exercise: dict | None = None
    lesson_type: LessonTypeEnum | None = None
    video_url: str | None = None
    estimated_minutes: int | None = None
    order_index: int | None = None
    is_premium: bool | None = None


class LessonResponse(BaseModel):
    id: UUID
    module_id: UUID
    title: str
    content_markdown: str
    content_html: str | None
    code_examples: list[dict] | None
    exercise: dict | None
    lesson_type: LessonTypeEnum
    video_url: str | None
    estimated_minutes: int | None
    order_index: int
    is_premium: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LessonSummary(BaseModel):
    """Lightweight lesson info for module listing."""
    id: UUID
    title: str
    lesson_type: LessonTypeEnum
    estimated_minutes: int | None
    order_index: int
    is_premium: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Module schemas
# ---------------------------------------------------------------------------

class ModuleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    order_index: int = 0
    day_number: int | None = None


class ModuleUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    order_index: int | None = None
    day_number: int | None = None


class ModuleResponse(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    description: str | None
    order_index: int
    day_number: int | None
    lesson_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class ModuleWithLessons(ModuleResponse):
    lessons: list[LessonSummary] = []


# ---------------------------------------------------------------------------
# Course schemas
# ---------------------------------------------------------------------------

class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    level: LevelEnum = LevelEnum.beginner
    estimated_duration_days: int | None = None
    thumbnail_url: str | None = None
    is_published: bool = False
    is_premium: bool = False
    order_index: int = 0
    tags: list[str] = []


class CourseUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    level: LevelEnum | None = None
    estimated_duration_days: int | None = None
    thumbnail_url: str | None = None
    is_published: bool | None = None
    is_premium: bool | None = None
    order_index: int | None = None
    tags: list[str] | None = None


class CourseListResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    description: str | None
    level: LevelEnum
    estimated_duration_days: int | None
    thumbnail_url: str | None
    is_premium: bool
    order_index: int
    tags: list[str]
    module_count: int = 0

    model_config = {"from_attributes": True}


class CourseResponse(CourseListResponse):
    is_published: bool
    modules: list[ModuleResponse] = []
    created_at: datetime
    updated_at: datetime
