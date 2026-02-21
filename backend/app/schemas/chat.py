from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Any
import uuid


class ChatSessionCreate(BaseModel):
    title: Optional[str] = None
    dataset_id: Optional[uuid.UUID] = None
    incident_id: Optional[uuid.UUID] = None


class ChatMessageCreate(BaseModel):
    content: str


class ChatSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    dataset_id: Optional[uuid.UUID]
    incident_id: Optional[uuid.UUID]
    title: Optional[str]
    created_at: datetime


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    evidence_refs: Optional[Any]
    model_name: Optional[str]
    created_at: datetime
