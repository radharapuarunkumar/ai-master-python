from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user, get_db
from app.models.chat import ChatMessage, ChatSession, MessageRole
from app.models.user import User
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse, ChatSessionCreate, ChatSessionResponse
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/tutor", tags=["AI Tutor"])


@router.post("", response_model=ResponseEnvelope[ChatSessionResponse])
async def create_chat_session(
    body: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[ChatSessionResponse]:
    """Start a new AI Tutor session."""
    session = ChatSession(
        user_id=current_user.id,
        title=body.title or "New Chat",
        context=body.context
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return ResponseEnvelope(data=ChatSessionResponse.model_validate(session))


@router.get("/{session_id}", response_model=ResponseEnvelope[ChatSessionResponse])
async def get_chat_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[ChatSessionResponse]:
    """Get a chat session and its messages."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id)
        .where(ChatSession.user_id == current_user.id)
    )
    session = result.scalars().first()
    if not session:
        raise NotFoundError("Chat session not found")
    return ResponseEnvelope(data=ChatSessionResponse.model_validate(session))


@router.post("/{session_id}/message", response_model=ResponseEnvelope[ChatMessageResponse])
async def send_message(
    session_id: UUID,
    body: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[ChatMessageResponse]:
    """Send a message and get a dummy AI response for now."""
    # Verify session
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id).where(ChatSession.user_id == current_user.id)
    )
    session = result.scalars().first()
    if not session:
        raise NotFoundError("Chat session not found")

    # Add user message
    user_msg = ChatMessage(session_id=session.id, role=MessageRole.user, content=body.content)
    db.add(user_msg)
    
    # Add dummy AI response
    ai_msg = ChatMessage(
        session_id=session.id, 
        role=MessageRole.assistant, 
        content=f"This is a simulated AI response to: '{body.content}'"
    )
    db.add(ai_msg)
    await db.commit()
    await db.refresh(ai_msg)
    
    return ResponseEnvelope(data=ChatMessageResponse.model_validate(ai_msg))
