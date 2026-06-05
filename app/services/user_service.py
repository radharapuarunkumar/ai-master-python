"""
User service: CRUD operations, role management, stats aggregation.
"""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.certificate import Certificate
from app.models.chat import ChatMessage, ChatSession
from app.models.progress import UserProgress, ProgressStatus
from app.models.user import User
from app.schemas.user import UserStats, UserUpdate

logger = logging.getLogger(__name__)


class UserService:
    """Handles all user data operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user(self, user_id: UUID) -> User:
        """Fetch a user by primary key.

        Raises:
            NotFoundError: If user does not exist.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Fetch a user by email address."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def update_user(self, user_id: UUID, data: UserUpdate) -> User:
        """Update the current user's own profile fields.

        Args:
            user_id: The user to update.
            data: Fields to change (all optional).

        Returns:
            Updated User object.
        """
        user = await self.get_user(user_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        await self.db.commit()
        await self.db.refresh(user)
        logger.info("User profile updated", extra={"user_id": str(user_id)})
        return user

    async def update_role(self, user_id: UUID, role: str) -> User:
        """Change a user's role (admin-only).

        Args:
            user_id: Target user's ID.
            role: New role string (admin / premium / free).

        Returns:
            Updated User object.
        """
        user = await self.get_user(user_id)
        from app.models.user import Role
        user.role = Role(role)
        await self.db.commit()
        await self.db.refresh(user)
        logger.info(
            "User role changed",
            extra={"user_id": str(user_id), "new_role": role},
        )
        return user

    async def list_users(
        self,
        page: int = 1,
        per_page: int = 20,
        role_filter: str | None = None,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        """List users with optional filters and pagination.

        Args:
            page: 1-indexed page number.
            per_page: Items per page (max 100).
            role_filter: Filter by role string.
            search: Search by name or email (ILIKE).

        Returns:
            Tuple of (users list, total count).
        """
        per_page = min(per_page, 100)
        query = select(User)

        if role_filter:
            from app.models.user import RoleEnum
            query = query.where(User.role == RoleEnum(role_filter))

        if search:
            pattern = f"%{search}%"
            query = query.where(
                User.email.ilike(pattern) | User.full_name.ilike(pattern)
            )

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        # Paginate
        offset = (page - 1) * per_page
        query = query.order_by(User.created_at.desc()).offset(offset).limit(per_page)
        result = await self.db.execute(query)
        users = list(result.scalars().all())

        return users, total

    async def deactivate_user(self, user_id: UUID) -> None:
        """Soft-deactivate a user account (sets is_active=False).

        Args:
            user_id: The user to deactivate.
        """
        user = await self.get_user(user_id)
        user.is_active = False
        await self.db.commit()
        logger.info("User deactivated", extra={"user_id": str(user_id)})

    async def get_user_stats(self, user_id: UUID) -> UserStats:
        """Aggregate dashboard statistics for a user.

        Args:
            user_id: Target user's ID.

        Returns:
            UserStats schema populated with current metrics.
        """
        # Courses enrolled (any progress record)
        courses_q = select(func.count(func.distinct(UserProgress.course_id))).where(
            UserProgress.user_id == user_id
        )
        courses_enrolled = (await self.db.execute(courses_q)).scalar_one() or 0

        # Lessons completed
        lessons_q = select(func.count()).where(
            UserProgress.user_id == user_id,
            UserProgress.lesson_id.isnot(None),
            UserProgress.status == ProgressStatus.completed,
        )
        lessons_completed = (await self.db.execute(lessons_q)).scalar_one() or 0

        # Total time spent
        time_q = select(func.coalesce(func.sum(UserProgress.time_spent_minutes), 0)).where(
            UserProgress.user_id == user_id
        )
        total_time = (await self.db.execute(time_q)).scalar_one() or 0

        # Certificates earned
        cert_q = select(func.count()).where(Certificate.user_id == user_id)
        certificates = (await self.db.execute(cert_q)).scalar_one() or 0

        # AI chats today
        from sqlalchemy import cast, Date
        from datetime import date
        today = date.today()
        chats_q = select(func.count()).where(
            ChatMessage.session_id.in_(
                select(ChatSession.id).where(ChatSession.user_id == user_id)
            ),
            cast(ChatMessage.created_at, Date) == today,
            ChatMessage.role == "user",
        )
        ai_chats_today = (await self.db.execute(chats_q)).scalar_one() or 0

        # AI generations today
        from app.models.ai_generation import AIGeneration
        gen_q = select(func.count()).where(
            AIGeneration.user_id == user_id,
            cast(AIGeneration.created_at, Date) == today,
        )
        ai_generations_today = (await self.db.execute(gen_q)).scalar_one() or 0

        # Streak calculation
        streak_data = await self._calculate_streak(user_id)

        return UserStats(
            courses_enrolled=courses_enrolled,
            lessons_completed=lessons_completed,
            current_streak=streak_data["current"],
            longest_streak=streak_data["longest"],
            total_time_minutes=total_time,
            certificates_earned=certificates,
            ai_chats_today=ai_chats_today,
            ai_generations_today=ai_generations_today,
        )

    async def _calculate_streak(self, user_id: UUID) -> dict:
        """Calculate current and longest learning streaks.

        Returns dict with 'current' and 'longest' streak counts.
        """
        from datetime import date, timedelta
        from sqlalchemy import cast, Date, distinct

        # Get distinct dates with completed lessons (ordered desc)
        dates_q = (
            select(cast(UserProgress.updated_at, Date).label("activity_date"))
            .where(
                UserProgress.user_id == user_id,
                UserProgress.status == ProgressStatus.completed,
            )
            .distinct()
            .order_by(cast(UserProgress.updated_at, Date).desc())
        )
        result = await self.db.execute(dates_q)
        activity_dates = [row.activity_date for row in result]

        if not activity_dates:
            return {"current": 0, "longest": 0}

        today = date.today()
        current_streak = 0
        longest_streak = 0
        streak = 0
        prev_date = None

        for d in sorted(set(activity_dates), reverse=True):
            if prev_date is None:
                # Start counting; allow today or yesterday as streak start
                if d >= today - timedelta(days=1):
                    streak = 1
                    current_streak = 1
                else:
                    break
            elif (prev_date - d).days == 1:
                streak += 1
                current_streak = streak
            else:
                break
            prev_date = d

        # Find longest streak across all history
        streak = 1
        sorted_dates = sorted(set(activity_dates))
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                streak += 1
                longest_streak = max(longest_streak, streak)
            else:
                streak = 1
        longest_streak = max(longest_streak, streak)

        return {"current": current_streak, "longest": longest_streak}
