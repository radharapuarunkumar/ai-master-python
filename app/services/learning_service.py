"""
Learning service: course/module/lesson management and progress tracking.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import cast, Date, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.course import Course, Module
from app.models.lesson import Lesson
from app.models.progress import ProgressStatus, UserProgress
from app.schemas.course import CourseCreate, CourseUpdate, LessonCreate, LessonUpdate, ModuleCreate
from app.schemas.progress import StreakResponse

logger = logging.getLogger(__name__)


class LearningService:
    """Handles all curriculum and progress tracking operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------

    async def list_courses(
        self,
        is_published: bool | None = True,
        level: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Course], int]:
        """List courses with optional filters.

        Args:
            is_published: If True, only published courses. None = all (admin).
            level: Filter by difficulty level.
            page: 1-indexed page.
            per_page: Items per page.

        Returns:
            (courses, total_count) tuple.
        """
        query = select(Course)

        if is_published is not None:
            query = query.where(Course.is_published == is_published)

        if level:
            from app.models.user import LevelEnum
            query = query.where(Course.level == LevelEnum(level))

        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar_one()

        offset = (page - 1) * per_page
        query = (
            query.order_by(Course.order_index.asc())
            .offset(offset)
            .limit(per_page)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_course(self, course_id_or_slug: str) -> Course:
        """Fetch a course by UUID or slug, including its modules.

        Raises:
            NotFoundError: If not found.
        """
        try:
            uid = UUID(course_id_or_slug)
            query = select(Course).where(Course.id == uid)
        except ValueError:
            query = select(Course).where(Course.slug == course_id_or_slug)

        query = query.options(selectinload(Course.modules))
        result = await self.db.execute(query)
        course = result.scalar_one_or_none()
        if not course:
            raise NotFoundError(f"Course '{course_id_or_slug}' not found")
        return course

    async def create_course(self, data: CourseCreate) -> Course:
        """Create a new course.

        Raises:
            ConflictError: If slug already exists.
        """
        # Check slug uniqueness
        existing = await self.db.execute(
            select(Course).where(Course.slug == data.slug)
        )
        if existing.scalar_one_or_none():
            from app.core.exceptions import ConflictError
            raise ConflictError(f"Course slug '{data.slug}' already exists")

        course = Course(**data.model_dump())
        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course)
        logger.info("Course created", extra={"course_id": str(course.id), "slug": course.slug})
        return course

    async def update_course(self, course_id: UUID, data: CourseUpdate) -> Course:
        """Update an existing course.

        Raises:
            NotFoundError: If course does not exist.
        """
        course = await self.get_course(str(course_id))
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(course, field, value)
        await self.db.commit()
        await self.db.refresh(course)
        return course

    async def delete_course(self, course_id: UUID) -> None:
        """Soft-delete a course by unpublishing it.

        Raises:
            NotFoundError: If not found.
        """
        course = await self.get_course(str(course_id))
        course.is_published = False
        await self.db.commit()

    # ------------------------------------------------------------------
    # Modules
    # ------------------------------------------------------------------

    async def list_modules(self, course_id: UUID) -> list[Module]:
        """List all modules in a course, ordered by order_index."""
        result = await self.db.execute(
            select(Module)
            .where(Module.course_id == course_id)
            .order_by(Module.order_index.asc())
        )
        return list(result.scalars().all())

    async def create_module(self, course_id: UUID, data: ModuleCreate) -> Module:
        """Add a module to a course.

        Raises:
            NotFoundError: If parent course not found.
        """
        await self.get_course(str(course_id))  # validate course exists
        module = Module(course_id=course_id, **data.model_dump())
        self.db.add(module)
        await self.db.commit()
        await self.db.refresh(module)
        return module

    # ------------------------------------------------------------------
    # Lessons
    # ------------------------------------------------------------------

    async def get_lesson(self, lesson_id: UUID, user_is_premium: bool = False) -> Lesson:
        """Fetch a lesson by ID, enforcing premium gate.

        Args:
            lesson_id: Target lesson UUID.
            user_is_premium: If False and lesson is premium, raises ForbiddenError.

        Raises:
            NotFoundError: If lesson not found.
            ForbiddenError: If premium lesson accessed by free user.
        """
        result = await self.db.execute(select(Lesson).where(Lesson.id == lesson_id))
        lesson = result.scalar_one_or_none()
        if not lesson:
            raise NotFoundError(f"Lesson {lesson_id} not found")
        if lesson.is_premium and not user_is_premium:
            raise ForbiddenError("This lesson requires a Premium subscription")
        return lesson

    async def list_lessons(self, module_id: UUID) -> list[Lesson]:
        """List all lessons in a module, ordered."""
        result = await self.db.execute(
            select(Lesson)
            .where(Lesson.module_id == module_id)
            .order_by(Lesson.order_index.asc())
        )
        return list(result.scalars().all())

    async def create_lesson(self, module_id: UUID, data: LessonCreate) -> Lesson:
        """Create a lesson inside a module."""
        # Validate module exists
        mod_result = await self.db.execute(select(Module).where(Module.id == module_id))
        if not mod_result.scalar_one_or_none():
            raise NotFoundError(f"Module {module_id} not found")

        lesson = Lesson(module_id=module_id, **data.model_dump())
        self.db.add(lesson)
        await self.db.commit()
        await self.db.refresh(lesson)
        return lesson

    async def update_lesson(self, lesson_id: UUID, data: LessonUpdate) -> Lesson:
        """Update a lesson's content."""
        result = await self.db.execute(select(Lesson).where(Lesson.id == lesson_id))
        lesson = result.scalar_one_or_none()
        if not lesson:
            raise NotFoundError(f"Lesson {lesson_id} not found")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(lesson, field, value)
        await self.db.commit()
        await self.db.refresh(lesson)
        return lesson

    # ------------------------------------------------------------------
    # Progress tracking
    # ------------------------------------------------------------------

    async def mark_lesson_started(self, user_id: UUID, lesson_id: UUID) -> UserProgress:
        """Record that a user has started a lesson.

        Creates a new progress record or updates an existing one.
        """
        lesson = await self.get_lesson(lesson_id, user_is_premium=True)  # fetch lesson

        # Find parent course via module
        mod_result = await self.db.execute(
            select(Module).where(Module.id == lesson.module_id)
        )
        module = mod_result.scalar_one_or_none()
        if not module:
            raise NotFoundError("Associated module not found")

        # Upsert progress record
        existing_q = await self.db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.lesson_id == lesson_id,
            )
        )
        progress = existing_q.scalar_one_or_none()

        if progress is None:
            from datetime import datetime, timezone
            progress = UserProgress(
                user_id=user_id,
                course_id=module.course_id,
                lesson_id=lesson_id,
                status=ProgressStatus.in_progress,
                started_at=datetime.now(timezone.utc),
            )
            self.db.add(progress)
        elif progress.status == ProgressStatus.not_started:
            from datetime import datetime, timezone
            progress.status = ProgressStatus.in_progress
            progress.started_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(progress)
        return progress

    async def mark_lesson_completed(
        self,
        user_id: UUID,
        lesson_id: UUID,
        score: int | None = None,
        time_spent_minutes: int | None = None,
    ) -> UserProgress:
        """Mark a lesson as completed and update course-level progress.

        Args:
            user_id: The learner.
            lesson_id: The completed lesson.
            score: Optional quiz/exercise score.
            time_spent_minutes: Optional time to add to cumulative total.

        Returns:
            Updated UserProgress record.
        """
        lesson = await self.get_lesson(lesson_id, user_is_premium=True)
        mod_result = await self.db.execute(
            select(Module).where(Module.id == lesson.module_id)
        )
        module = mod_result.scalar_one_or_none()
        if not module:
            raise NotFoundError("Associated module not found")

        existing_q = await self.db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.lesson_id == lesson_id,
            )
        )
        progress = existing_q.scalar_one_or_none()

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        if progress is None:
            progress = UserProgress(
                user_id=user_id,
                course_id=module.course_id,
                lesson_id=lesson_id,
                status=ProgressStatus.completed,
                progress_percent=100.0,
                started_at=now,
                completed_at=now,
            )
            self.db.add(progress)
        else:
            progress.status = ProgressStatus.completed
            progress.progress_percent = 100.0
            progress.completed_at = now

        if score is not None:
            progress.score = score
        if time_spent_minutes is not None:
            progress.time_spent_minutes += time_spent_minutes

        await self.db.commit()
        await self.db.refresh(progress)

        # Update overall course progress percentage
        await self._recalculate_course_progress(user_id, module.course_id)

        return progress

    async def get_course_progress(self, user_id: UUID, course_id: UUID) -> dict:
        """Get detailed progress for a user in a specific course."""
        course = await self.get_course(str(course_id))

        total_lessons_q = (
            select(func.count(Lesson.id))
            .join(Module, Lesson.module_id == Module.id)
            .where(Module.course_id == course_id)
        )
        total_lessons = (await self.db.execute(total_lessons_q)).scalar_one() or 0

        completed_q = select(func.count()).where(
            UserProgress.user_id == user_id,
            UserProgress.course_id == course_id,
            UserProgress.lesson_id.isnot(None),
            UserProgress.status == ProgressStatus.completed,
        )
        completed = (await self.db.execute(completed_q)).scalar_one() or 0

        time_q = select(func.coalesce(func.sum(UserProgress.time_spent_minutes), 0)).where(
            UserProgress.user_id == user_id,
            UserProgress.course_id == course_id,
        )
        total_time = (await self.db.execute(time_q)).scalar_one() or 0

        overall_percent = (completed / total_lessons * 100) if total_lessons > 0 else 0

        return {
            "course": course,
            "overall_percent": round(overall_percent, 2),
            "lessons_completed": completed,
            "total_lessons": total_lessons,
            "time_spent_minutes": total_time,
        }

    async def get_all_progress(self, user_id: UUID) -> list[UserProgress]:
        """Get all progress records for a user."""
        result = await self.db.execute(
            select(UserProgress)
            .where(UserProgress.user_id == user_id)
            .order_by(UserProgress.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_streak(self, user_id: UUID) -> StreakResponse:
        """Calculate the user's current and longest learning streak."""
        dates_q = (
            select(cast(UserProgress.updated_at, Date).label("d"))
            .where(
                UserProgress.user_id == user_id,
                UserProgress.status == ProgressStatus.completed,
            )
            .distinct()
            .order_by(cast(UserProgress.updated_at, Date).desc())
        )
        result = await self.db.execute(dates_q)
        activity_dates = sorted({row.d for row in result}, reverse=True)

        today = date.today()
        current_streak = 0
        longest_streak = 0

        if activity_dates:
            # Current streak
            streak = 0
            for i, d in enumerate(activity_dates):
                expected = today - timedelta(days=i)
                if d == expected:
                    streak += 1
                else:
                    break
            current_streak = streak

            # Longest streak
            streak = 1
            sorted_asc = sorted(activity_dates)
            for i in range(1, len(sorted_asc)):
                if (sorted_asc[i] - sorted_asc[i - 1]).days == 1:
                    streak += 1
                    longest_streak = max(longest_streak, streak)
                else:
                    streak = 1
            longest_streak = max(longest_streak, streak if activity_dates else 0)

        last_activity = activity_dates[0] if activity_dates else None
        week_ago = today - timedelta(days=6)
        activity_this_week = [d for d in activity_dates if d >= week_ago]

        return StreakResponse(
            current_streak=current_streak,
            longest_streak=longest_streak,
            last_activity_date=last_activity,
            activity_this_week=activity_this_week,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _recalculate_course_progress(self, user_id: UUID, course_id: UUID) -> None:
        """Recompute and update the overall course-level progress record."""
        total_lessons_q = (
            select(func.count(Lesson.id))
            .join(Module, Lesson.module_id == Module.id)
            .where(Module.course_id == course_id)
        )
        total = (await self.db.execute(total_lessons_q)).scalar_one() or 0

        completed_q = select(func.count()).where(
            UserProgress.user_id == user_id,
            UserProgress.course_id == course_id,
            UserProgress.lesson_id.isnot(None),
            UserProgress.status == ProgressStatus.completed,
        )
        completed = (await self.db.execute(completed_q)).scalar_one() or 0

        percent = (completed / total * 100) if total > 0 else 0

        # Upsert course-level progress (lesson_id=None)
        course_prog_q = await self.db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.course_id == course_id,
                UserProgress.lesson_id.is_(None),
            )
        )
        course_progress = course_prog_q.scalar_one_or_none()

        if course_progress is None:
            from datetime import datetime, timezone
            course_progress = UserProgress(
                user_id=user_id,
                course_id=course_id,
                status=ProgressStatus.in_progress,
                progress_percent=percent,
                started_at=datetime.now(timezone.utc),
            )
            self.db.add(course_progress)
        else:
            course_progress.progress_percent = percent
            if percent >= 100:
                from datetime import datetime, timezone
                course_progress.status = ProgressStatus.completed
                course_progress.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
