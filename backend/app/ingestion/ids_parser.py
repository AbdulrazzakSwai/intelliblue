import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from .normalizer import NormalizedEvent


def _parse_time(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    for fmt in ["%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"]:
        try:
            dt = datetime.strptime(val, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


PRIORITY_TO_SEVERITY = {1: "CRITICAL", 2: "HIGH", 3: "MEDIUM", 4: "LOW"}


def parse_suricata(content: str) -> List[NormalizedEvent]:
    """Parse Suricata EVE JSON (NDJSON or array), filter event_type=alert."""
    events: List[NormalizedEvent] = []
    records: List[Dict] = []

    content = content.strip()
    if content.startswith("["):
        try:
            records = json.loads(content)
        except json.JSONDecodeError:
            pass
    else:
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    for raw in records:
        if not isinstance(raw, dict):
            continue
        if raw.get("event_type") != "alert":
            continue
        alert = raw.get("alert", {})
        priority = alert.get("severity", 3)
        evt = NormalizedEvent(
            source_type="SURICATA",
            event_time=_parse_time(raw.get("timestamp")),
            src_ip=raw.get("src_ip"),
            dst_ip=raw.get("dest_ip"),
            src_port=raw.get("src_port"),
            dst_port=raw.get("dest_port"),
            protocol=raw.get("proto"),
            signature_id=str(alert.get("signature_id", "")),
            signature=alert.get("signature"),
            category=alert.get("category"),
            ids_priority=priority,
            severity_hint=PRIORITY_TO_SEVERITY.get(priority, "MEDIUM"),
            event_type="ids_alert",
            message=alert.get("signature"),
            raw_json=raw,
        )
        events.append(evt)
    return events


def parse_snort(content: str) -> List[NormalizedEvent]:
    """Parse Snort JSON alerts."""
    events: List[NormalizedEvent] = []
    records: List[Dict] = []

    content = content.strip()
    if content.startswith("["):
        try:
            records = json.loads(content)
        except json.JSONDecodeError:
            pass
    else:
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    for raw in records:
        if not isinstance(raw, dict):
            continue
        priority = raw.get("priority", 3)
        evt = NormalizedEvent(
            source_type="SNORT",
            event_time=_parse_time(raw.get("timestamp")),
            src_ip=raw.get("src_ip") or raw.get("src"),
            dst_ip=raw.get("dst_ip") or raw.get("dst"),
            src_port=raw.get("src_port"),
            dst_port=raw.get("dst_port"),
            protocol=raw.get("protocol") or raw.get("proto"),
            signature_id=str(raw.get("sid", "")),
            signature=raw.get("msg"),
            category=raw.get("classtype"),
            ids_priority=priority,
            severity_hint=PRIORITY_TO_SEVERITY.get(priority, "MEDIUM"),
            event_type="ids_alert",
            message=raw.get("msg"),
            raw_json=raw,
        )
        events.append(evt)
    return events
