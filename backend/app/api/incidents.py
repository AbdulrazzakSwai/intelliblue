import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models.user import User
from ..models.incident import Incident, IncidentStatus
from ..models.event import Event
from ..models.incident_event import IncidentEvent
from ..schemas.incident import IncidentOut, IncidentDetail, IncidentUpdate
from ..middleware.rbac import require_l1, require_l2, get_current_user
from ..middleware.audit import record_audit
from ..llm.summarizer import summarize_incident

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/", response_model=List[IncidentOut])
async def list_incidents(
    dataset_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    incident_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l1),
):
    stmt = select(Incident)
    if dataset_id:
        stmt = stmt.where(Incident.dataset_id == str(dataset_id))
    if status:
        stmt = stmt.where(Incident.status == status)
    if severity:
        stmt = stmt.where(Incident.severity == severity)
    if incident_type:
        stmt = stmt.where(Incident.incident_type == incident_type)
    stmt = stmt.order_by(Incident.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{incident_id}", response_model=IncidentDetail)
async def get_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l1),
):
    incident = await db.get(Incident, str(incident_id))
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/{incident_id}/acknowledge", response_model=IncidentOut)
async def acknowledge_incident(
    incident_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l1),
):
    incident = await db.get(Incident, str(incident_id))
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident.status = IncidentStatus.ACK.value
    incident.acknowledged_by = current_user.id
    incident.acknowledged_at = datetime.now(timezone.utc)
    await db.flush()
    await record_audit(
        db, "INCIDENT_ACK", user_id=str(current_user.id),
        target_type="Incident", target_id=str(incident_id),
        ip_addr=request.client.host if request.client else None,
    )
    return incident


@router.patch("/{incident_id}", response_model=IncidentOut)
async def update_incident(
    incident_id: uuid.UUID,
    data: IncidentUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l2),
):
    incident = await db.get(Incident, str(incident_id))
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    before = {"status": incident.status, "severity": incident.severity}
    if data.status is not None:
        incident.status = data.status
    if data.severity is not None:
        incident.severity = data.severity
    if data.incident_type is not None:
        incident.incident_type = data.incident_type
    if data.assigned_to is not None:
        incident.assigned_to = data.assigned_to
    incident.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await record_audit(
        db, "INCIDENT_UPDATE", user_id=str(current_user.id),
        target_type="Incident", target_id=str(incident_id),
        before_json=before,
        after_json={"status": incident.status, "severity": incident.severity},
        ip_addr=request.client.host if request.client else None,
    )
    return incident


@router.post("/{incident_id}/close", response_model=IncidentOut)
async def close_incident(
    incident_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l2),
):
    incident = await db.get(Incident, str(incident_id))
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident.status = IncidentStatus.CLOSED.value
    incident.closed_by = current_user.id
    incident.closed_at = datetime.now(timezone.utc)
    incident.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await record_audit(
        db, "INCIDENT_CLOSE", user_id=str(current_user.id),
        target_type="Incident", target_id=str(incident_id),
        ip_addr=request.client.host if request.client else None,
    )
    return incident


@router.post("/{incident_id}/summarize")
async def trigger_summarize(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l1),
):
    summary = await summarize_incident(db, str(incident_id))
    if not summary:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"id": str(summary.id), "narrative": summary.narrative, "model_name": summary.model_name}


@router.get("/{incident_id}/events")
async def get_incident_events(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l1),
):
    result = await db.execute(
        select(Event)
        .join(IncidentEvent, IncidentEvent.event_id == Event.id)
        .where(IncidentEvent.incident_id == str(incident_id))
        .order_by(Event.event_time)
    )
    return result.scalars().all()
