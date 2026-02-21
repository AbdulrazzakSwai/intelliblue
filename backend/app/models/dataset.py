import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, Integer, ForeignKey, Text
from sqlalchemy import JSON

from sqlalchemy.orm import relationship
from ..database import Base


class DatasetStatus(str, enum.Enum):
    UPLOADING = "UPLOADING"
    PARSING = "PARSING"
    CORRELATING = "CORRELATING"
    SUMMARIZING = "SUMMARIZING"
    READY = "READY"
    ERROR = "ERROR"


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SAEnum(DatasetStatus), default=DatasetStatus.UPLOADING, nullable=False)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    event_count = Column(Integer, default=0)
    incident_count = Column(Integer, default=0)
    parse_errors = Column(JSON, default=list)

    uploader = relationship("User", back_populates="datasets", foreign_keys=[uploaded_by])
    raw_files = relationship("RawFile", back_populates="dataset", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="dataset", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="dataset", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="dataset")
