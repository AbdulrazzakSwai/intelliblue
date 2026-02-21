import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models.user import User, UserRole
from ..models.incident_note import IncidentNote, NoteType
from ..schemas.incident import NoteCreate, NoteOut
from ..middleware.rbac import require_l1, get_current_user
from ..middleware.audit import record_audit

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/incidents/{incident_id}/notes", response_model=NoteOut, status_code=201)
async def add_note(
    incident_id: uuid.UUID,
    data: NoteCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l1),
):
    # L1 can only add TRIAGE notes; L2+ can add INVESTIGATION notes
    if data.note_type == "INVESTIGATION" and current_user.role == UserRole.L1:
        raise HTTPException(status_code=403, detail="L1 can only add TRIAGE notes")

    note = IncidentNote(
        id=str(uuid.uuid4()),
        incident_id=incident_id,
        note_type=NoteType(data.note_type),
        content=data.content,
        author_id=current_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(note)
    await db.flush()
    await record_audit(
        db, "NOTE_ADD", user_id=str(current_user.id),
        target_type="IncidentNote", target_id=str(note.id),
        ip_addr=request.client.host if request.client else None,
    )
    return note


@router.get("/incidents/{incident_id}/notes", response_model=List[NoteOut])
async def list_notes(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l1),
):
    result = await db.execute(
        select(IncidentNote)
        .where(IncidentNote.incident_id == str(incident_id))
        .order_by(IncidentNote.created_at)
    )
    return result.scalars().all()
