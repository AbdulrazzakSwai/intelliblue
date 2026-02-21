import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SAEnum

from sqlalchemy.orm import relationship
from ..database import Base
import enum


class UserRole(str, enum.Enum):
    L1 = "L1"
    L2 = "L2"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False)
    full_name = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True), nullable=True)

    datasets = relationship("Dataset", back_populates="uploader", foreign_keys="Dataset.uploaded_by")
    notes = relationship("IncidentNote", back_populates="author")
    chat_sessions = relationship("ChatSession", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
