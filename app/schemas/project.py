from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import DifficultyEnum


class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    difficulty: DifficultyEnum = DifficultyEnum.beginner
    starter_code: Optional[str] = None
    solution_code: Optional[str] = None
    requirements: Optional[dict] = None
    tags: Optional[list[str]] = None
    estimated_hours: Optional[float] = None
    is_ai_generated: bool = False
    order_index: int = 0


class ProjectCreate(ProjectBase):
    course_id: Optional[UUID] = None


class ProjectResponse(ProjectBase):
    id: UUID
    course_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
