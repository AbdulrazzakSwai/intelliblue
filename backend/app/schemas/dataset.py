from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any
import uuid


class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str]
    status: str
    uploaded_by: uuid.UUID
    uploaded_at: datetime
    event_count: int
    incident_count: int
    parse_errors: Optional[Any]


class DatasetList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    status: str
    uploaded_at: datetime
    event_count: int
    incident_count: int
