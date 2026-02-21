"""
Rule 3: IDS-confirmed alert incidents.

Each IDS alert seeds an incident. Related auth/web events within ±window minutes
are pulled in as corroboration.
"""
import uuid
from datetime import timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.event import Event
from ...models.incident import Incident, IncidentStatus
from ...models.incident_event import IncidentEvent
from ..scoring import compute_severity


RULE_ID = "ids_confirmed_v1"


async def run(
    db: AsyncSession,
    dataset_id: str,
    config: Dict[str, Any],
) -> List[Incident]:
    corr_window = config.get("ids_correlation_window_minutes", 10)

    result = await db.execute(
        select(Event).where(
            Event.dataset_id == dataset_id,
            Event.source_type.in_(["SURICATA", "SNORT"]),
        )
    )
    ids_events = result.scalars().all()

    incidents = []
    for ids_ev in ids_events:
        title = f"IDS Alert: {ids_ev.signature or ids_ev.message or 'Unknown'} from {ids_ev.src_ip or 'unknown'}"

        existing = await db.execute(
            select(Incident).where(
                Incident.dataset_id == dataset_id,
                Incident.rule_id == RULE_ID,
                Incident.title == title,
            )
        )
        if existing.scalar_one_or_none():
            continue

        confidence = max(40, 100 - (ids_ev.ids_priority or 3) * 15)
        severity = compute_severity(confidence, ids_corroborated=True)

        explanation = (
            f"IDS alert: {ids_ev.signature or ids_ev.message}. "
            f"Category: {ids_ev.category}. "
            f"Priority: {ids_ev.ids_priority}. "
            f"Source: {ids_ev.src_ip} -> {ids_ev.dst_ip}. "
            f"Confidence: {confidence}%."
        )

        incident = Incident(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            title=title,
            status=IncidentStatus.NEW.value,
            severity=severity,
            incident_type="ids_alert",
            confidence=confidence,
            rule_id=RULE_ID,
            rule_explanation=explanation,
        )
        db.add(incident)
        await db.flush()

        # Primary IDS event
        ie = IncidentEvent(
            id=str(uuid.uuid4()),
            incident_id=incident.id,
            event_id=ids_ev.id,
            relevance="primary",
        )
        db.add(ie)

        # Pull corroborating events within ±window
        if ids_ev.event_time:
            t_start = ids_ev.event_time - timedelta(minutes=corr_window)
            t_end = ids_ev.event_time + timedelta(minutes=corr_window)
            corr_result = await db.execute(
                select(Event).where(
                    Event.dataset_id == dataset_id,
                    Event.src_ip == ids_ev.src_ip,
                    Event.event_time >= t_start,
                    Event.event_time <= t_end,
                    Event.id != ids_ev.id,
                )
            )
            for ev in corr_result.scalars().all():
                ie2 = IncidentEvent(
                    id=str(uuid.uuid4()),
                    incident_id=incident.id,
                    event_id=ev.id,
                    relevance="corroborating",
                )
                db.add(ie2)

        incidents.append(incident)

    return incidents
