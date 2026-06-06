from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user, get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.schemas.project import ProjectResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=ResponseEnvelope[list[ProjectResponse]])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ResponseEnvelope[list[ProjectResponse]]:
    """List all available python projects."""
    result = await db.execute(select(Project).order_by(Project.order_index))
    projects = result.scalars().all()
    return ResponseEnvelope(data=[ProjectResponse.model_validate(p) for p in projects])


@router.get("/{project_id}", response_model=ResponseEnvelope[ProjectResponse])
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ResponseEnvelope[ProjectResponse]:
    """Get project details."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise NotFoundError("Project not found")
    return ResponseEnvelope(data=ProjectResponse.model_validate(project))
