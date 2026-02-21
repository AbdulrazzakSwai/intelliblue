from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Any
import uuid


class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    incident_type: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None


class NoteCreate(BaseModel):
    content: str
    note_type: str  # TRIAGE or INVESTIGATION


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    note_type: str
    content: str
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class AISummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    summary_json: Optional[Any]
    narrative: Optional[str]
    model_name: Optional[str]
    prompt_version: Optional[str]
    generation_time_sec: Optional[float]
    created_at: datetime


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dataset_id: uuid.UUID
    title: str
    status: str
    severity: str
    incident_type: Optional[str]
    confidence: int
    rule_id: Optional[str]
    rule_explanation: Optional[str]
    created_at: datetime
    updated_at: datetime
    acknowledged_by: Optional[uuid.UUID]
    acknowledged_at: Optional[datetime]
    assigned_to: Optional[uuid.UUID]
    closed_by: Optional[uuid.UUID]
    closed_at: Optional[datetime]


class IncidentDetail(IncidentOut):
    notes: List[NoteOut] = []
    ai_summaries: List[AISummaryOut] = []
