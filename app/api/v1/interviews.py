from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.video_session import InterviewQuestion, InterviewSession, SessionType, VideoSession
from app.schemas.common import ResponseEnvelope
from app.schemas.interview import InterviewAnswerSubmit, InterviewQuestionResponse, InterviewSessionCreate, InterviewSessionResponse

router = APIRouter(prefix="/interviews", tags=["Interviews"])


@router.post("", response_model=ResponseEnvelope[InterviewSessionResponse])
async def create_interview(
    body: InterviewSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[InterviewSessionResponse]:
    """Start a new mock interview session."""
    # Create video session first
    vs = VideoSession(user_id=current_user.id, session_type=SessionType.interview)
    db.add(vs)
    await db.flush()
    
    # Create interview wrapper
    interview = InterviewSession(
        video_session_id=vs.id,
        user_id=current_user.id,
        interview_type=body.interview_type,
        difficulty=body.difficulty,
    )
    db.add(interview)
    await db.flush()
    
    # Add a dummy question
    q = InterviewQuestion(
        interview_id=interview.id,
        question_text="Explain how decorators work in Python.",
        expected_answer="A decorator is a function that takes another function and extends its behavior without explicitly modifying it.",
        order_index=1
    )
    db.add(q)
    await db.commit()
    await db.refresh(interview)
    
    return ResponseEnvelope(data=InterviewSessionResponse.model_validate(interview))


@router.get("/{interview_id}", response_model=ResponseEnvelope[InterviewSessionResponse])
async def get_interview(
    interview_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[InterviewSessionResponse]:
    """Get interview session details."""
    result = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.id == interview_id)
        .where(InterviewSession.user_id == current_user.id)
    )
    interview = result.scalars().first()
    if not interview:
        raise NotFoundError("Interview not found")
    return ResponseEnvelope(data=InterviewSessionResponse.model_validate(interview))


@router.post("/questions/{question_id}/answer", response_model=ResponseEnvelope[InterviewQuestionResponse])
async def submit_answer(
    question_id: UUID,
    body: InterviewAnswerSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[InterviewQuestionResponse]:
    """Submit an answer to an interview question."""
    result = await db.execute(select(InterviewQuestion).where(InterviewQuestion.id == question_id))
    question = result.scalars().first()
    if not question:
        raise NotFoundError("Question not found")
        
    question.user_answer = body.answer
    question.score = 8.5  # Dummy score
    question.ai_evaluation = "Good answer! You covered the basics well."
    await db.commit()
    await db.refresh(question)
    
    return ResponseEnvelope(data=InterviewQuestionResponse.model_validate(question))
