import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ResponseEnvelope, SessionTypeEnum, SessionStatusEnum
from app.schemas.interview import InterviewAnswerSubmit, InterviewQuestionResponse, InterviewSessionCreate, InterviewSessionResponse, VideoSessionResponse

router = APIRouter(prefix="/interviews", tags=["Interviews"])

@router.post("", response_model=ResponseEnvelope[InterviewSessionResponse])
async def create_interview(
    body: InterviewSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[InterviewSessionResponse]:
    """Start a new mock interview session."""
    interview_id = uuid.uuid4()
    video_session_id = uuid.uuid4()
    
    video_session = VideoSessionResponse(
        id=video_session_id,
        user_id=current_user.id,
        session_type=SessionTypeEnum.interview,
        status=SessionStatusEnum.in_progress,
        created_at=datetime.now(timezone.utc),
    )
    
    questions = [
        InterviewQuestionResponse(
            id=uuid.uuid4(),
            interview_id=interview_id,
            question_text="Explain your approach to system design or coding.",
            expected_answer="A good explanation.",
            order_index=1,
            asked_at=datetime.now(timezone.utc),
        )
    ]
    
    interview = InterviewSessionResponse(
        id=interview_id,
        video_session_id=video_session_id,
        user_id=current_user.id,
        interview_type=body.interview_type,
        difficulty=body.difficulty,
        created_at=datetime.now(timezone.utc),
        video_session=video_session,
        questions=questions,
    )
    
    return ResponseEnvelope(data=interview)


@router.get("/{interview_id}", response_model=ResponseEnvelope[InterviewSessionResponse])
async def get_interview(
    interview_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[InterviewSessionResponse]:
    """Get interview session details."""
    video_session_id = uuid.uuid4()
    
    video_session = VideoSessionResponse(
        id=video_session_id,
        user_id=current_user.id,
        session_type=SessionTypeEnum.interview,
        status=SessionStatusEnum.completed,
        created_at=datetime.now(timezone.utc),
    )
    
    questions = [
        InterviewQuestionResponse(
            id=uuid.uuid4(),
            interview_id=interview_id,
            question_text="What are decorators?",
            expected_answer="A decorator is a function that takes another function...",
            user_answer="It's a wrapper.",
            score=7.0,
            ai_evaluation="Good start but lacks detail.",
            order_index=1,
            asked_at=datetime.now(timezone.utc),
        )
    ]
    
    interview = InterviewSessionResponse(
        id=interview_id,
        video_session_id=video_session_id,
        user_id=current_user.id,
        interview_type="technical",
        difficulty="intermediate",
        overall_score=75.0,
        strengths={"communication": "good"},
        improvements={"technical_depth": "needs work"},
        ai_feedback="Overall a solid performance.",
        created_at=datetime.now(timezone.utc),
        video_session=video_session,
        questions=questions,
    )
    
    return ResponseEnvelope(data=interview)


@router.post("/questions/{question_id}/answer", response_model=ResponseEnvelope[InterviewQuestionResponse])
async def submit_answer(
    question_id: UUID,
    body: InterviewAnswerSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[InterviewQuestionResponse]:
    """Submit an answer to an interview question."""
    
    question = InterviewQuestionResponse(
        id=question_id,
        interview_id=uuid.uuid4(),
        question_text="What are decorators?",
        expected_answer="A decorator is a function...",
        user_answer=body.answer,
        score=8.5,
        ai_evaluation="Good answer! You covered the basics well.",
        order_index=1,
        asked_at=datetime.now(timezone.utc),
    )
    
    return ResponseEnvelope(data=question)
