from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import MessageRoleEnum


class ChatMessageBase(BaseModel):
    role: MessageRoleEnum
    content: str
    metadata_: Optional[dict] = None


class ChatMessageCreate(BaseModel):
    content: str


class ChatMessageResponse(ChatMessageBase):
    id: UUID
    session_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionBase(BaseModel):
    title: Optional[str] = None
    context: Optional[dict] = None
    is_active: bool = True


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionResponse(ChatSessionBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageResponse] = []

    model_config = ConfigDict(from_attributes=True)
