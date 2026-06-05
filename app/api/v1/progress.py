"""
Progress tracking endpoints: lesson start/complete, course progress, streaks.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.schemas.progress import (
    CompleteLesson,
    CourseProgressResponse,
    ProgressResponse,
    StreakResponse,
)
from app.services.learning_service import LearningService

router = APIRouter(prefix="/progress", tags=["Progress"])


@router.get("", response_model=ResponseEnvelope[list[ProgressResponse]])
async def get_all_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[list[ProgressResponse]]:
    """Get all progress records for the current user across all courses."""
    svc = LearningService(db=db)
    records = await svc.get_all_progress(current_user.id)
    return ResponseEnvelope(data=[ProgressResponse.model_validate(r) for r in records])


@router.get(
    "/course/{course_id}",
    response_model=ResponseEnvelope[CourseProgressResponse],
)
async def get_course_progress(
    course_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[CourseProgressResponse]:
    """Get detailed progress for the current user in a specific course."""
    svc = LearningService(db=db)
    data = await svc.get_course_progress(current_user.id, course_id)
    return ResponseEnvelope(
        data=CourseProgressResponse(
            course=data["course"],
            overall_percent=data["overall_percent"],
            lessons_completed=data["lessons_completed"],
            total_lessons=data["total_lessons"],
            time_spent_minutes=data["time_spent_minutes"],
            started_at=None,
            completed_at=None,
        )
    )


@router.post(
    "/lesson/{lesson_id}/start",
    response_model=ResponseEnvelope[ProgressResponse],
    status_code=status.HTTP_200_OK,
)
async def start_lesson(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[ProgressResponse]:
    """Mark a lesson as started for the current user."""
    svc = LearningService(db=db)
    progress = await svc.mark_lesson_started(current_user.id, lesson_id)
    return ResponseEnvelope(data=ProgressResponse.model_validate(progress))


@router.post(
    "/lesson/{lesson_id}/complete",
    response_model=ResponseEnvelope[ProgressResponse],
    status_code=status.HTTP_200_OK,
)
async def complete_lesson(
    lesson_id: UUID,
    body: CompleteLesson = CompleteLesson(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[ProgressResponse]:
    """Mark a lesson as completed. Optionally include score and time spent."""
    svc = LearningService(db=db)
    progress = await svc.mark_lesson_completed(
        user_id=current_user.id,
        lesson_id=lesson_id,
        score=body.score,
        time_spent_minutes=body.time_spent_minutes,
    )
    return ResponseEnvelope(data=ProgressResponse.model_validate(progress))


@router.get("/streak", response_model=ResponseEnvelope[StreakResponse])
async def get_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[StreakResponse]:
    """Get the current user's learning streak data."""
    svc = LearningService(db=db)
    streak = await svc.get_streak(current_user.id)
    return ResponseEnvelope(data=streak)
