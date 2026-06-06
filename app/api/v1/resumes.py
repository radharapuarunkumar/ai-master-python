import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user, get_db
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
    dummy_resume = ResumeResponse(
        id=uuid.uuid4(),
        user_id=current_user.id,
        title="Software Engineer Resume",
        content={"experience": "Worked as a Python Developer for 2 years."},
        template_id="modern",
        target_job_title="Backend Engineer",
        target_job_description="Looking for Python backend roles.",
        pdf_url="https://example.com/resume.pdf",
        ats_score=85.0,
        ats_analysis={"score": 85.0, "feedback": "Good keyword matching."},
        version=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return ResponseEnvelope(data=[dummy_resume])


@router.post("", response_model=ResponseEnvelope[ResumeResponse])
async def create_resume(
    body: ResumeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[ResumeResponse]:
    """Create a new resume."""
    dummy_resume = ResumeResponse(
        id=uuid.uuid4(),
        user_id=current_user.id,
        title=body.title,
        content=body.content,
        template_id=body.template_id,
        target_job_title=body.target_job_title,
        target_job_description=body.target_job_description,
        pdf_url=None,
        ats_score=None,
        ats_analysis=None,
        version=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return ResponseEnvelope(data=dummy_resume)

@router.put("/{resume_id}", response_model=ResponseEnvelope[ResumeResponse])
async def update_resume(
    resume_id: UUID,
    body: ResumeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[ResumeResponse]:
    """Update a resume."""
    dummy_resume = ResumeResponse(
        id=resume_id,
        user_id=current_user.id,
        title=body.title,
        content=body.content,
        template_id=body.template_id,
        target_job_title=body.target_job_title,
        target_job_description=body.target_job_description,
        pdf_url="https://example.com/resume.pdf",
        ats_score=95.0,
        ats_analysis={"score": 95.0, "feedback": "Excellent."},
        version=2,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return ResponseEnvelope(data=dummy_resume)
