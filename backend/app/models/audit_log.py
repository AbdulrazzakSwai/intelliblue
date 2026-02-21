import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index, JSON

from sqlalchemy.orm import relationship
from ..database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action_type = Column(String(64), nullable=False)
    target_type = Column(String(64), nullable=True)
    target_id = Column(String(128), nullable=True)
    before_json = Column(JSON, nullable=True)
    after_json = Column(JSON, nullable=True)
    details = Column(Text, nullable=True)
    ip_addr = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_log_created_at", "created_at"),
    )
