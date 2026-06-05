"""
User management endpoints: own profile, admin user management.
"""
from __future__ import annotations

import math
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_admin, require_role, Role
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import PaginationMeta, ResponseEnvelope
from app.schemas.user import AdminUserUpdate, RoleUpdate, UserDetail, UserListItem, UserStats, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=ResponseEnvelope[UserDetail])
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[UserDetail]:
    """Return the authenticated user's full profile."""
    return ResponseEnvelope(data=UserDetail.model_validate(current_user))


@router.patch("/me", response_model=ResponseEnvelope[UserDetail])
async def update_my_profile(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[UserDetail]:
    """Update the current user's editable profile fields."""
    svc = UserService(db=db)
    user = await svc.update_user(current_user.id, body)
    return ResponseEnvelope(data=UserDetail.model_validate(user))


@router.get("/me/stats", response_model=ResponseEnvelope[UserStats])
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[UserStats]:
    """Return dashboard statistics for the current user."""
    svc = UserService(db=db)
    stats = await svc.get_user_stats(current_user.id)
    return ResponseEnvelope(data=stats)


@router.get(
    "",
    response_model=ResponseEnvelope[list[UserListItem]],
    dependencies=[Depends(require_admin)],
)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: str | None = Query(None, description="Filter by role"),
    search: str | None = Query(None, description="Search by name or email"),
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[list[UserListItem]]:
    """[Admin] List all users with optional filters and pagination."""
    svc = UserService(db=db)
    users, total = await svc.list_users(
        page=page, per_page=per_page, role_filter=role, search=search
    )
    return ResponseEnvelope(
        data=[UserListItem.model_validate(u) for u in users],
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=math.ceil(total / per_page),
        ).model_dump(),
    )


@router.get(
    "/{user_id}",
    response_model=ResponseEnvelope[UserDetail],
    dependencies=[Depends(require_admin)],
)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[UserDetail]:
    """[Admin] Get any user's full profile."""
    svc = UserService(db=db)
    user = await svc.get_user(user_id)
    return ResponseEnvelope(data=UserDetail.model_validate(user))


@router.patch(
    "/{user_id}/role",
    response_model=ResponseEnvelope[UserDetail],
    dependencies=[Depends(require_admin)],
)
async def update_user_role(
    user_id: UUID,
    body: RoleUpdate,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope[UserDetail]:
    """[Admin] Change a user's role (free / premium / admin)."""
    svc = UserService(db=db)
    user = await svc.update_role(user_id, body.role.value)
    return ResponseEnvelope(data=UserDetail.model_validate(user))


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin)],
)
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """[Admin] Soft-deactivate a user account."""
    svc = UserService(db=db)
    await svc.deactivate_user(user_id)
    return {"status": "success", "data": {"message": "User deactivated"}}
