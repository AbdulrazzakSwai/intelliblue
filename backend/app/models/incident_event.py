import uuid
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint

from sqlalchemy.orm import relationship
from ..database import Base


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    relevance = Column(String(32), default="corroborating")

    incident = relationship("Incident", back_populates="incident_events")
    event = relationship("Event", back_populates="incident_events")

    __table_args__ = (
        UniqueConstraint("incident_id", "event_id", name="uq_incident_event"),
    )
