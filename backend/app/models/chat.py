import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SAEnum, JSON

from sqlalchemy.orm import relationship
from ..database import Base


class MessageRole(str, enum.Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=True)
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=True)
    title = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="chat_sessions")
    dataset = relationship("Dataset", back_populates="chat_sessions")
    incident = relationship("Incident", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(SAEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    evidence_refs = Column(JSON, default=dict)
    model_name = Column(String(256), nullable=True)
    prompt_version = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session = relationship("ChatSession", back_populates="messages")
