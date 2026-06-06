from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ResumeBase(BaseModel):
    title: str
    content: Optional[dict] = None
    template_id: Optional[str] = None
    target_job_title: Optional[str] = None
    target_job_description: Optional[str] = None


class ResumeCreate(ResumeBase):
    pass


class ResumeResponse(ResumeBase):
    id: UUID
    user_id: UUID
    pdf_url: Optional[str] = None
    ats_score: Optional[float] = None
    ats_analysis: Optional[dict] = None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
