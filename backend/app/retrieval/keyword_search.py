"""
Keyword-based retrieval over incidents and events in the database.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from ..models.incident import Incident
from ..models.event import Event


async def search_incidents(
    db: AsyncSession,
    query: str,
    dataset_id: Optional[str] = None,
    incident_id: Optional[str] = None,
    limit: int = 5,
) -> List[Incident]:
    keywords = query.lower().split()
    stmt = select(Incident)
    conditions = []
    for kw in keywords:
        conditions.append(
            or_(
                Incident.title.ilike(f"%{kw}%"),
                Incident.rule_explanation.ilike(f"%{kw}%"),
                Incident.incident_type.ilike(f"%{kw}%"),
            )
        )
    if conditions:
        from sqlalchemy import and_
        stmt = stmt.where(or_(*conditions))
    if dataset_id:
        stmt = stmt.where(Incident.dataset_id == dataset_id)
    if incident_id:
        stmt = stmt.where(Incident.id == incident_id)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def search_events(
    db: AsyncSession,
    query: str,
    dataset_id: Optional[str] = None,
    limit: int = 10,
) -> List[Event]:
    keywords = query.lower().split()
    stmt = select(Event)
    conditions = []
    for kw in keywords:
        conditions.append(
            or_(
                Event.message.ilike(f"%{kw}%"),
                Event.signature.ilike(f"%{kw}%"),
                Event.src_ip.ilike(f"%{kw}%"),
                Event.username.ilike(f"%{kw}%"),
                Event.url_path.ilike(f"%{kw}%"),
            )
        )
    if conditions:
        from sqlalchemy import and_
        stmt = stmt.where(or_(*conditions))
    if dataset_id:
        stmt = stmt.where(Event.dataset_id == dataset_id)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
