"""
Course, module, and lesson endpoints.
"""
from __future__ import annotations

import math
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_admin
from app.dependencies import get_current_user, get_db, get_optional_user
from app.models.user import User, Role
from app.schemas.common import PaginationMeta, ResponseEnvelope
from app.schemas.course import (
    CourseCreate,
    CourseListResponse,
    CourseResponse,
    CourseUpdate,
    LessonCreate,
    LessonResponse,
    LessonSummary,
    LessonUpdate,
    ModuleCreate,
    ModuleResponse,
    ModuleWithLessons,
)
from app.services.learning_service import LearningService

router = APIRouter(prefix="/courses", tags=["Courses"])


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------

@router.get("", response_model=ResponseEnvelope[list[CourseListResponse]])
async def list_courses(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    level: str | None = Query(None, description="beginner | intermediate | advanced"),
    optional_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[list[CourseListResponse]]:
    """List available courses. Public users only see published courses."""
    is_admin = optional_user and optional_user.role == Role.admin
    # Admins see all; everyone else sees published only
    is_published = None if is_admin else True

    svc = LearningService(db=db)
    courses, total = await svc.list_courses(
        is_published=is_published, level=level, page=page, per_page=per_page
    )

    items = []
    for c in courses:
        item = CourseListResponse.model_validate(c)
        item.module_count = len(c.modules) if hasattr(c, "modules") else 0
        items.append(item)

    return ResponseEnvelope(
        data=items,
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=math.ceil(total / per_page) if total else 1,
        ).model_dump(),
    )


@router.post(
    "",
    response_model=ResponseEnvelope[CourseResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_course(
    body: CourseCreate,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[CourseResponse]:
    """[Admin] Create a new course."""
    svc = LearningService(db=db)
    course = await svc.create_course(body)
    return ResponseEnvelope(data=CourseResponse.model_validate(course))


@router.get("/{slug}", response_model=ResponseEnvelope[CourseResponse])
async def get_course(
    slug: str,
    db: AsyncSession = Depends(get_db),
    optional_user: User | None = Depends(get_optional_user),
) -> ResponseEnvelope[CourseResponse]:
    """Get a course by slug or UUID, including its modules."""
    svc = LearningService(db=db)
    course = await svc.get_course(slug)
    resp = CourseResponse.model_validate(course)
    resp.modules = [ModuleResponse.model_validate(m) for m in course.modules]
    return ResponseEnvelope(data=resp)


@router.put(
    "/{course_id}",
    response_model=ResponseEnvelope[CourseResponse],
    dependencies=[Depends(require_admin)],
)
async def update_course(
    course_id: UUID,
    body: CourseUpdate,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[CourseResponse]:
    """[Admin] Update a course's details."""
    svc = LearningService(db=db)
    course = await svc.update_course(course_id, body)
    return ResponseEnvelope(data=CourseResponse.model_validate(course))


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin)],
)
async def delete_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """[Admin] Soft-delete (unpublish) a course."""
    svc = LearningService(db=db)
    await svc.delete_course(course_id)
    return {"status": "success", "data": {"message": "Course unpublished"}}


# ---------------------------------------------------------------------------
# Modules
# ---------------------------------------------------------------------------

@router.get("/{course_id}/modules", response_model=ResponseEnvelope[list[ModuleResponse]])
async def list_modules(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ResponseEnvelope[list[ModuleResponse]]:
    """List all modules in a course."""
    svc = LearningService(db=db)
    modules = await svc.list_modules(course_id)
    return ResponseEnvelope(data=[ModuleResponse.model_validate(m) for m in modules])


@router.post(
    "/{course_id}/modules",
    response_model=ResponseEnvelope[ModuleResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_module(
    course_id: UUID,
    body: ModuleCreate,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[ModuleResponse]:
    """[Admin] Add a module to a course."""
    svc = LearningService(db=db)
    module = await svc.create_module(course_id, body)
    return ResponseEnvelope(data=ModuleResponse.model_validate(module))


# ---------------------------------------------------------------------------
# Lessons (nested under /modules and standalone)
# ---------------------------------------------------------------------------

@router.get(
    "/modules/{module_id}/lessons",
    response_model=ResponseEnvelope[list[LessonSummary]],
)
async def list_lessons(
    module_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ResponseEnvelope[list[LessonSummary]]:
    """List all lessons in a module (summary view)."""
    svc = LearningService(db=db)
    lessons = await svc.list_lessons(module_id)
    return ResponseEnvelope(data=[LessonSummary.model_validate(l) for l in lessons])


@router.get("/lessons/{lesson_id}", response_model=ResponseEnvelope[LessonResponse])
async def get_lesson(
    lesson_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[LessonResponse]:
    """Get full lesson content. Premium lessons require premium access."""
    is_premium = current_user.role in (RoleEnum.premium, RoleEnum.admin)
    svc = LearningService(db=db)
    lesson = await svc.get_lesson(lesson_id, user_is_premium=is_premium)
    return ResponseEnvelope(data=LessonResponse.model_validate(lesson))


@router.post(
    "/lessons",
    response_model=ResponseEnvelope[LessonResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_lesson(
    module_id: UUID = Query(..., description="Module to add lesson to"),
    body: LessonCreate = ...,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[LessonResponse]:
    """[Admin] Create a new lesson in a module."""
    svc = LearningService(db=db)
    lesson = await svc.create_lesson(module_id, body)
    return ResponseEnvelope(data=LessonResponse.model_validate(lesson))


@router.put(
    "/lessons/{lesson_id}",
    response_model=ResponseEnvelope[LessonResponse],
    dependencies=[Depends(require_admin)],
)
async def update_lesson(
    lesson_id: UUID,
    body: LessonUpdate,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[LessonResponse]:
    """[Admin] Update a lesson's content and metadata."""
    svc = LearningService(db=db)
    lesson = await svc.update_lesson(lesson_id, body)
    return ResponseEnvelope(data=LessonResponse.model_validate(lesson))
