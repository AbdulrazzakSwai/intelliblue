import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models.user import User
from ..models.incident import Incident
from ..models.event import Event
from ..models.incident_event import IncidentEvent
from ..models.incident_note import IncidentNote
from ..models.incident_ai_summary import IncidentAISummary
from ..middleware.rbac import require_l2
from ..reporting.pdf_generator import generate_incident_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/incidents/{incident_id}/pdf")
async def export_incident_pdf(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l2),
):
    incident = await db.get(Incident, str(incident_id))
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    events_result = await db.execute(
        select(Event)
        .join(IncidentEvent, IncidentEvent.event_id == Event.id)
        .where(IncidentEvent.incident_id == str(incident_id))
        .order_by(Event.event_time)
    )
    events = events_result.scalars().all()

    notes_result = await db.execute(
        select(IncidentNote).where(IncidentNote.incident_id == str(incident_id))
    )
    notes = notes_result.scalars().all()

    summary_result = await db.execute(
        select(IncidentAISummary)
        .where(IncidentAISummary.incident_id == str(incident_id))
        .order_by(IncidentAISummary.created_at.desc())
        .limit(1)
    )
    ai_summary = summary_result.scalar_one_or_none()

    pdf_bytes = generate_incident_pdf(incident, events, notes, ai_summary)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=incident_{incident_id}.pdf"},
    )
