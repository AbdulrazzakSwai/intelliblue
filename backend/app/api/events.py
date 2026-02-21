import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models.user import User
from ..models.event import Event
from ..schemas.event import EventOut
from ..middleware.rbac import require_l1

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=List[EventOut])
async def list_events(
    dataset_id: Optional[uuid.UUID] = Query(None),
    src_ip: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l1),
):
    stmt = select(Event)
    if dataset_id:
        stmt = stmt.where(Event.dataset_id == str(dataset_id))
    if src_ip:
        stmt = stmt.where(Event.src_ip == src_ip)
    if event_type:
        stmt = stmt.where(Event.event_type == event_type)
    stmt = stmt.order_by(Event.event_time.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
