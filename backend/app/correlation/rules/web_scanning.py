"""
Rule 2: Web scanning / reconnaissance detection.

Detects high unique URL hits, 404/401 spikes, and suspicious user agents
within a configurable time window.
"""
import uuid
from datetime import timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.event import Event
from ...models.incident import Incident, IncidentStatus
from ...models.incident_event import IncidentEvent
from ..scoring import compute_confidence, compute_severity


RULE_ID = "web_scanning_v1"


async def run(
    db: AsyncSession,
    dataset_id: str,
    config: Dict[str, Any],
) -> List[Incident]:
    window_minutes = config.get("web_scan_window_minutes", 5)
    url_threshold = config.get("web_scan_url_threshold", 20)
    error_threshold = config.get("web_scan_error_threshold", 10)

    result = await db.execute(
        select(Event).where(
            Event.dataset_id == dataset_id,
            Event.source_type == "WEB_LOG",
            Event.src_ip.isnot(None),
        ).order_by(Event.src_ip, Event.event_time)
    )
    web_events = result.scalars().all()

    # Group by src_ip
    ip_events: Dict[str, List[Event]] = {}
    for ev in web_events:
        ip_events.setdefault(ev.src_ip, []).append(ev)

    incidents = []
    for src_ip, evts in ip_events.items():
        evts_sorted = sorted([e for e in evts if e.event_time], key=lambda e: e.event_time)
        if not evts_sorted:
            continue

        for i, start_evt in enumerate(evts_sorted):
            window_end = start_evt.event_time + timedelta(minutes=window_minutes)
            window_evts = [e for e in evts_sorted[i:] if e.event_time <= window_end]

            unique_urls = len(set(e.url_path for e in window_evts if e.url_path))
            error_count = sum(1 for e in window_evts if e.http_status in (404, 401, 403))
            suspicious_ua = any(
                e.event_type == "suspicious_ua" for e in window_evts
            )

            triggered = unique_urls >= url_threshold or error_count >= error_threshold or suspicious_ua
            if not triggered:
                continue

            existing = await db.execute(
                select(Incident).where(
                    Incident.dataset_id == dataset_id,
                    Incident.rule_id == RULE_ID,
                    Incident.title.contains(src_ip),
                )
            )
            if existing.scalar_one_or_none():
                break

            # Check IDS corroboration
            ids_result = await db.execute(
                select(Event).where(
                    Event.dataset_id == dataset_id,
                    Event.source_type.in_(["SURICATA", "SNORT"]),
                    Event.src_ip == src_ip,
                )
            )
            ids_events = ids_result.scalars().all()
            sources = ["web"]
            if ids_events:
                sources.append("ids")

            confidence = compute_confidence(len(window_evts), url_threshold, sources)
            severity = compute_severity(confidence, ids_corroborated=bool(ids_events))

            explanation = (
                f"Web scanning detected from {src_ip}: "
                f"{unique_urls} unique URLs, {error_count} 4xx errors "
                f"in {window_minutes} min window. "
                f"Suspicious UA: {suspicious_ua}. "
                f"Confidence: {confidence}%."
            )

            incident = Incident(
                id=str(uuid.uuid4()),
                dataset_id=dataset_id,
                title=f"Web Scanning / Reconnaissance from {src_ip}",
                status=IncidentStatus.NEW.value,
                severity=severity,
                incident_type="web_scanning",
                confidence=confidence,
                rule_id=RULE_ID,
                rule_explanation=explanation,
            )
            db.add(incident)
            await db.flush()

            for ev in window_evts:
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
            break

    return incidents
