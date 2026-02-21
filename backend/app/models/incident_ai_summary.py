import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, JSON

from sqlalchemy.orm import relationship
from ..database import Base


class IncidentAISummary(Base):
    __tablename__ = "incident_ai_summaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    summary_json = Column(JSON, nullable=True)
    narrative = Column(Text, nullable=True)
    model_name = Column(String(256), nullable=True)
    prompt_version = Column(String(64), nullable=True)
    generation_time_sec = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    incident = relationship("Incident", back_populates="ai_summaries")
