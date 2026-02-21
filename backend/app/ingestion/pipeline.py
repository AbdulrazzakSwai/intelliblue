"""
Core ingestion pipeline.

ingest_event() is the atomic function that processes a single NormalizedEvent
into the database. It is used by batch uploads now and will be used by streaming agents later.
"""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .normalizer import NormalizedEvent
from .siem_parser import parse_siem_json
from .web_parser import parse_web_log
from .ids_parser import parse_suricata, parse_snort
from ..models.event import Event


async def ingest_event(
    db: AsyncSession,
    normalized: NormalizedEvent,
    dataset_id: str,
    raw_file_id: Optional[str] = None,
) -> Event:
    """
    Persist a single NormalizedEvent to the database.
    This is the atomic pipeline function designed for both batch and streaming use.
    """
    event = Event(
        id=str(uuid.uuid4()),
        dataset_id=dataset_id,
        raw_file_id=raw_file_id,
        event_time=normalized.event_time,
        source_type=normalized.source_type,
        host=normalized.host,
        username=str(normalized.username)[:256] if normalized.username else None,
        src_ip=str(normalized.src_ip)[:64] if normalized.src_ip else None,
        dst_ip=str(normalized.dst_ip)[:64] if normalized.dst_ip else None,
        src_port=normalized.src_port,
        dst_port=normalized.dst_port,
        event_type=normalized.event_type,
        severity_hint=normalized.severity_hint,
        http_method=normalized.http_method,
        url_path=normalized.url_path,
        http_status=normalized.http_status,
        user_agent=normalized.user_agent,
        response_size=normalized.response_size,
        signature_id=normalized.signature_id,
        signature=normalized.signature,
        category=normalized.category,
        ids_priority=normalized.ids_priority,
        protocol=normalized.protocol,
        message=normalized.message,
        raw_json=normalized.raw_json,
        extras=normalized.extras,
    )
    db.add(event)
    await db.flush()
    return event


async def ingest_batch(
    db: AsyncSession,
    normalized_events: list,
    dataset_id: str,
    raw_file_id: Optional[str] = None,
) -> list:
    """Ingest a batch of NormalizedEvents by calling ingest_event for each."""
    persisted = []
    for ne in normalized_events:
        e = await ingest_event(db, ne, dataset_id, raw_file_id)
        persisted.append(e)
    return persisted


def parse_content(content: str, file_type: str) -> list:
    """Parse raw file content by type into NormalizedEvents."""
    if file_type == "SIEM_JSON":
        return parse_siem_json(content)
    elif file_type == "WEB_LOG":
        return parse_web_log(content)
    elif file_type == "SURICATA":
        return parse_suricata(content)
    elif file_type == "SNORT":
        return parse_snort(content)
    return []
