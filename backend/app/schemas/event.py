from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any
import uuid


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dataset_id: uuid.UUID
    event_time: Optional[datetime]
    source_type: Optional[str]
    host: Optional[str]
    username: Optional[str]
    src_ip: Optional[str]
    dst_ip: Optional[str]
    src_port: Optional[int]
    dst_port: Optional[int]
    event_type: Optional[str]
    severity_hint: Optional[str]
    http_method: Optional[str]
    url_path: Optional[str]
    http_status: Optional[int]
    user_agent: Optional[str]
    response_size: Optional[int]
    signature_id: Optional[str]
    signature: Optional[str]
    category: Optional[str]
    ids_priority: Optional[int]
    protocol: Optional[str]
    message: Optional[str]
