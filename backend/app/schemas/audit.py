from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any
import uuid


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    action_type: str
    target_type: Optional[str]
    target_id: Optional[str]
    details: Optional[str]
    ip_addr: Optional[str]
    created_at: datetime
