"""
Rule 1: Brute-force / password spraying detection.

Detects repeated login failures from a single IP or targeting a single user
within a configurable time window.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ...models.event import Event
from ...models.incident import Incident, IncidentStatus, IncidentSeverity
from ...models.incident_event import IncidentEvent
from ..scoring import compute_confidence, compute_severity


RULE_ID = "brute_force_v1"


async def run(
    db: AsyncSession,
    dataset_id: str,
    config: Dict[str, Any],
) -> List[Incident]:
    window_minutes = config.get("brute_force_window_minutes", 10)
    threshold = config.get("brute_force_threshold", 5)

    # Find login_failure events grouped by src_ip
    result = await db.execute(
        select(Event.src_ip, Event.event_time)
        .where(Event.dataset_id == dataset_id)
        .where(Event.event_type == "login_failure")
        .where(Event.src_ip.isnot(None))
        .order_by(Event.src_ip, Event.event_time)
    )
    rows = result.fetchall()

    # Group by src_ip and find windows
    ip_events: Dict[str, List[datetime]] = {}
    for src_ip, event_time in rows:
        if event_time:
            ip_events.setdefault(src_ip, []).append(event_time)

    incidents = []
    for src_ip, times in ip_events.items():
        times.sort()
        # Sliding window
        for i, start in enumerate(times):
            window_end = start + timedelta(minutes=window_minutes)
            window_events = [t for t in times[i:] if t <= window_end]
            if len(window_events) >= threshold:
                # Check if an incident already exists for this ip/dataset
                existing = await db.execute(
                    select(Incident).where(
                        Incident.dataset_id == dataset_id,
                        Incident.rule_id == RULE_ID,
                        Incident.title.contains(src_ip),
                    )
                )
                if existing.scalar_one_or_none():
                    break

                # Corroborate with IDS
                ids_result = await db.execute(
                    select(Event).where(
                        Event.dataset_id == dataset_id,
                        Event.source_type.in_(["SURICATA", "SNORT"]),
                        Event.src_ip == src_ip,
                    )
                )
                ids_events = ids_result.scalars().all()

                sources = ["auth"]
                if ids_events:
                    sources.append("ids")

                confidence = compute_confidence(len(window_events), threshold, sources)
                severity = compute_severity(confidence, ids_corroborated=bool(ids_events))

                explanation = (
                    f"Detected {len(window_events)} login failures from {src_ip} "
                    f"within {window_minutes} minutes (threshold: {threshold}). "
                    f"Corroboration sources: {', '.join(sources)}. "
                    f"Confidence: {confidence}%."
                )

                incident = Incident(
                    id=str(uuid.uuid4()),
                    dataset_id=dataset_id,
                    title=f"Brute Force Attack from {src_ip}",
                    status=IncidentStatus.NEW.value,
                    severity=severity,
                    incident_type="brute_force",
                    confidence=confidence,
                    rule_id=RULE_ID,
                    rule_explanation=explanation,
                )
                db.add(incident)
                await db.flush()

                # Link events
                failure_events = await db.execute(
                    select(Event).where(
                        Event.dataset_id == dataset_id,
                        Event.event_type == "login_failure",
                        Event.src_ip == src_ip,
                    )
                )
                for ev in failure_events.scalars().all():
                    ie = IncidentEvent(
                        id=str(uuid.uuid4()),
                        incident_id=incident.id,
                        event_id=ev.id,
                        relevance="primary",
                    )
                    db.add(ie)

                for ev in ids_events:
                    ie = IncidentEvent(
                        id=str(uuid.uuid4()),
                        incident_id=incident.id,
                        event_id=ev.id,
                        relevance="corroborating",
                    )
                    db.add(ie)

                incidents.append(incident)
                break  # One incident per IP

    return incidents
