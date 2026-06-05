"""
Progress-related Pydantic schemas.
"""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ProgressStatusEnum
from app.schemas.course import CourseListResponse


class ProgressResponse(BaseModel):
    id: UUID
    user_id: UUID
    course_id: UUID
    lesson_id: UUID | None
    status: ProgressStatusEnum
    progress_percent: float
    score: int | None
    time_spent_minutes: int
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class LessonProgressItem(BaseModel):
    lesson_id: UUID
    lesson_title: str
    status: ProgressStatusEnum
    score: int | None
    time_spent_minutes: int
    completed_at: datetime | None


class CourseProgressResponse(BaseModel):
    course: CourseListResponse
    overall_percent: float
    lessons_completed: int
    total_lessons: int
    time_spent_minutes: int
    started_at: datetime | None
    completed_at: datetime | None
    lesson_progress: list[LessonProgressItem] = []


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    last_activity_date: date | None
    activity_this_week: list[date] = []


class MilestoneResponse(BaseModel):
    id: str
    title: str
    description: str
    icon: str
    earned_at: datetime | None
    is_earned: bool


class CompleteLesson(BaseModel):
    score: int | None = None
    time_spent_minutes: int | None = None
