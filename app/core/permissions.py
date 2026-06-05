"""Role-based permission system using FastAPI dependency injection.

Roles are ordered hierarchically:  admin > premium > free.
Use ``require_role(Role.premium)`` as a route dependency to gate access.
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, status

if TYPE_CHECKING:
    from app.models.user import User


class Role(str, enum.Enum):
    """Application-wide user roles (ordered by privilege)."""

    admin = "admin"
    premium = "premium"
    free = "free"


# Higher number ⇒ more privilege.
ROLE_HIERARCHY: dict[Role, int] = {
    Role.free: 0,
    Role.premium: 1,
    Role.admin: 2,
}


def _get_role_level(role: Role | str) -> int:
    """Return the numeric privilege level for a role string or enum."""
    if isinstance(role, str):
        role = Role(role)
    return ROLE_HIERARCHY[role]


def require_role(minimum_role: Role):
    """Dependency factory that rejects users below *minimum_role*.

    Usage::

        @router.get("/admin/dashboard", dependencies=[Depends(require_role(Role.admin))])
        async def admin_dashboard(): ...
    """

    async def _guard(
        current_user: "User" = Depends(_lazy_get_current_user),
    ) -> "User":
        user_level = _get_role_level(current_user.role)
        required_level = _get_role_level(minimum_role)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires at least '{minimum_role.value}' role.",
            )
        return current_user

    return _guard


def _lazy_get_current_user():
    """Late-import wrapper to avoid circular dependency with ``app.dependencies``."""
    from app.dependencies import get_current_user  # noqa: WPS433

    return Depends(get_current_user)


# ── Convenience shortcuts ─────────────────────────────────────────────────

require_admin = require_role(Role.admin)
"""Dependency that requires the ``admin`` role."""

require_premium = require_role(Role.premium)
"""Dependency that requires at least the ``premium`` role."""
