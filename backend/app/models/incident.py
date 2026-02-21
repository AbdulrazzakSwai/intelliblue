import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, DateTime, Integer, ForeignKey, Index, Text, Float
)

from sqlalchemy.orm import relationship
from ..database import Base


class IncidentStatus(str, enum.Enum):
    NEW = "NEW"
    ACK = "ACK"
    INVESTIGATING = "INVESTIGATING"
    CLOSED = "CLOSED"


class IncidentSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(512), nullable=False)
    status = Column(String(20), default=IncidentStatus.NEW.value, nullable=False)
    severity = Column(String(20), default=IncidentSeverity.MEDIUM.value, nullable=False)
    incident_type = Column(String(64), nullable=True)
    confidence = Column(Integer, default=50)
    rule_id = Column(String(64), nullable=True)
    rule_explanation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    acknowledged_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(String(36), ForeignKey("users.id"), nullable=True)
    closed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    dataset = relationship("Dataset", back_populates="incidents")
    incident_events = relationship("IncidentEvent", back_populates="incident", cascade="all, delete-orphan")
    notes = relationship("IncidentNote", back_populates="incident", cascade="all, delete-orphan")
    ai_summaries = relationship("IncidentAISummary", back_populates="incident", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="incident")

    __table_args__ = (
        Index("ix_incidents_dataset_status", "dataset_id", "status"),
    )
