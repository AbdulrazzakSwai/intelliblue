import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models.user import User
from ..models.chat import ChatSession, ChatMessage, MessageRole
from ..schemas.chat import ChatSessionCreate, ChatMessageCreate, ChatSessionOut, ChatMessageOut
from ..middleware.rbac import require_l1
from ..llm.chat_engine import chat_response

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=ChatSessionOut, status_code=201)
async def create_session(
    data: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l1),
):
    session = ChatSession(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        dataset_id=data.dataset_id,
        incident_id=data.incident_id,
        title=data.title or "New Chat",
    )
    db.add(session)
    await db.flush()
    return session


@router.get("/sessions", response_model=List[ChatSessionOut])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l1),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
    )
    return result.scalars().all()


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageOut, status_code=201)
async def send_message(
    session_id: uuid.UUID,
    data: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l1),
):
    session = await db.get(ChatSession, str(session_id))
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    # Store user message
    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=str(session_id),
        role=MessageRole.USER,
        content=data.content,
    )
    db.add(user_msg)
    await db.flush()

    # Generate AI response
    ai_msg = await chat_response(
        db,
        str(session_id),
        data.content,
        dataset_id=str(session.dataset_id) if session.dataset_id else None,
        incident_id=str(session.incident_id) if session.incident_id else None,
    )
    return ai_msg


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageOut])
async def get_messages(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l1),
):
    session = await db.get(ChatSession, str(session_id))
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == str(session_id))
        .order_by(ChatMessage.created_at)
    )
    return result.scalars().all()
