from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user, get_db
from app.models.resume import Resume
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.schemas.resume import ResumeCreate, ResumeResponse

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.get("", response_model=ResponseEnvelope[list[ResumeResponse]])
async def list_resumes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[ResumeResponse]]:
    """Get user's resumes."""
    result = await db.execute(select(Resume).where(Resume.user_id == current_user.id))
    resumes = result.scalars().all()
    return ResponseEnvelope(data=[ResumeResponse.model_validate(r) for r in resumes])


@router.post("", response_model=ResponseEnvelope[ResumeResponse])
async def create_resume(
    body: ResumeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[ResumeResponse]:
    """Create a new resume."""
    resume = Resume(
        user_id=current_user.id,
        title=body.title,
        content=body.content,
        template_id=body.template_id,
        target_job_title=body.target_job_title,
        target_job_description=body.target_job_description,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return ResponseEnvelope(data=ResumeResponse.model_validate(resume))
