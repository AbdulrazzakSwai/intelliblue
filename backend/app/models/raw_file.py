import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, BigInteger, ForeignKey

from sqlalchemy.orm import relationship
from ..database import Base


class FileType(str, enum.Enum):
    SIEM_JSON = "SIEM_JSON"
    WEB_LOG = "WEB_LOG"
    SURICATA = "SURICATA"
    SNORT = "SNORT"


class RawFile(Base):
    __tablename__ = "raw_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(512), nullable=False)
    file_type = Column(SAEnum(FileType), nullable=False)
    sha256 = Column(String(64), nullable=False)
    stored_path = Column(String(1024), nullable=False)
    size_bytes = Column(BigInteger, default=0)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    dataset = relationship("Dataset", back_populates="raw_files")
    events = relationship("Event", back_populates="raw_file")
