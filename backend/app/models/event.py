import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, DateTime, Integer, ForeignKey, Index, Text, JSON
)

from sqlalchemy.orm import relationship
from ..database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False)
    raw_file_id = Column(String(36), ForeignKey("raw_files.id"), nullable=True)
    event_time = Column(DateTime(timezone=True), nullable=True, index=True)
    source_type = Column(String(32), nullable=True)
    host = Column(String(256), nullable=True)
    username = Column(String(256), nullable=True, index=True)
    src_ip = Column(String(64), nullable=True, index=True)
    dst_ip = Column(String(64), nullable=True)
    src_port = Column(Integer, nullable=True)
    dst_port = Column(Integer, nullable=True)
    event_type = Column(String(64), nullable=True)
    severity_hint = Column(String(32), nullable=True)
    http_method = Column(String(16), nullable=True)
    url_path = Column(Text, nullable=True)
    http_status = Column(Integer, nullable=True)
    user_agent = Column(Text, nullable=True)
    response_size = Column(Integer, nullable=True)
    signature_id = Column(String(64), nullable=True)
    signature = Column(Text, nullable=True)
    category = Column(String(128), nullable=True)
    ids_priority = Column(Integer, nullable=True)
    protocol = Column(String(32), nullable=True)
    message = Column(Text, nullable=True)
    raw_json = Column(JSON, nullable=True)
    extras = Column(JSON, nullable=True)

    dataset = relationship("Dataset", back_populates="events")
    raw_file = relationship("RawFile", back_populates="events")
    incident_events = relationship("IncidentEvent", back_populates="event")

    __table_args__ = (
        Index("ix_events_dataset_time", "dataset_id", "event_time"),
        Index("ix_events_src_ip_time", "src_ip", "event_time"),
    )
