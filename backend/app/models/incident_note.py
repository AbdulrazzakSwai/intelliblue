import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SAEnum

from sqlalchemy.orm import relationship
from ..database import Base


class NoteType(str, enum.Enum):
    TRIAGE = "TRIAGE"
    INVESTIGATION = "INVESTIGATION"


class IncidentNote(Base):
    __tablename__ = "incident_notes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    note_type = Column(SAEnum(NoteType), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    incident = relationship("Incident", back_populates="notes")
    author = relationship("User", back_populates="notes")
