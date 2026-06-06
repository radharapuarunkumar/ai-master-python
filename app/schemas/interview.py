from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import DifficultyEnum, InterviewTypeEnum, SessionStatusEnum, SessionTypeEnum


class VideoSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    session_type: SessionTypeEnum
    status: SessionStatusEnum
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    livekit_room_name: Optional[str] = None
    recording_url: Optional[str] = None
    ai_summary: Optional[str] = None
    topic: Optional[str] = None
    metadata_: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewQuestionResponse(BaseModel):
    id: UUID
    interview_id: UUID
    question_text: str
    expected_answer: Optional[str] = None
    user_answer: Optional[str] = None
    score: Optional[float] = None
    ai_evaluation: Optional[str] = None
    order_index: int
    asked_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InterviewSessionCreate(BaseModel):
    interview_type: InterviewTypeEnum
    difficulty: DifficultyEnum = DifficultyEnum.intermediate


class InterviewSessionResponse(BaseModel):
    id: UUID
    video_session_id: UUID
    user_id: UUID
    interview_type: InterviewTypeEnum
    difficulty: DifficultyEnum
    overall_score: Optional[float] = None
    strengths: Optional[dict] = None
    improvements: Optional[dict] = None
    ai_feedback: Optional[str] = None
    created_at: datetime
    video_session: Optional[VideoSessionResponse] = None
    questions: list[InterviewQuestionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class InterviewAnswerSubmit(BaseModel):
    answer: str
