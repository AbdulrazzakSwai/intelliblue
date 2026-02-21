import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
from .normalizer import NormalizedEvent
from ..config import settings


def _load_mapping() -> Dict[str, List[str]]:
    path = Path(settings.siem_mapping_path)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    # Default mapping
    return {
        "timestamp": ["timestamp", "time", "@timestamp", "event_time", "datetime", "date"],
        "username": ["user", "username", "src_user", "account", "user_name", "subject"],
        "src_ip": ["src_ip", "source_ip", "src", "sourceIPAddress", "client_ip", "remote_addr"],
        "dst_ip": ["dst_ip", "dest_ip", "destination_ip", "dst", "dest"],
        "host": ["host", "hostname", "computer", "machine", "device"],
        "event_type": ["action", "event_type", "eventType", "type", "category"],
        "severity": ["severity", "priority", "level", "criticality"],
        "message": ["message", "msg", "description", "detail", "log"],
        "src_port": ["src_port", "source_port", "sport"],
        "dst_port": ["dst_port", "dest_port", "dport"],
    }


def _extract(raw: Dict[str, Any], candidates: List[str]) -> Optional[Any]:
    for key in candidates:
        if key in raw:
            return raw[key]
    return None


def _parse_time(val) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        try:
            return datetime.fromtimestamp(val, tz=timezone.utc)
        except Exception:
            return None
    if isinstance(val, str):
        for fmt in [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
        ]:
            try:
                dt = datetime.strptime(val, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
    return None


def _classify_event(raw: Dict[str, Any], mapping: Dict) -> str:
    action = str(_extract(raw, mapping.get("event_type", [])) or "").lower()
    if any(k in action for k in ["fail", "failure", "invalid", "denied", "reject"]):
        return "login_failure"
    if any(k in action for k in ["success", "logon", "login", "authenticated"]):
        return "login_success"
    if any(k in action for k in ["alert", "alarm", "attack", "threat"]):
        return "alert"
    return "generic"


def parse_siem_json(content: str) -> List[NormalizedEvent]:
    """Parse SIEM JSON export (NDJSON or JSON array)."""
    mapping = _load_mapping()
    events: List[NormalizedEvent] = []
    raw_records: List[Dict] = []

    content = content.strip()
    if content.startswith("["):
        try:
            raw_records = json.loads(content)
        except json.JSONDecodeError:
            pass
    else:
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                raw_records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    known_fields = set()
    for candidates in mapping.values():
        known_fields.update(candidates)

    for raw in raw_records:
        if not isinstance(raw, dict):
            continue

        ts = _parse_time(_extract(raw, mapping.get("timestamp", [])))
        extras = {k: v for k, v in raw.items() if k not in known_fields}

        evt = NormalizedEvent(
            source_type="SIEM_JSON",
            event_time=ts,
            username=_extract(raw, mapping.get("username", [])),
            src_ip=_extract(raw, mapping.get("src_ip", [])),
            dst_ip=_extract(raw, mapping.get("dst_ip", [])),
            host=_extract(raw, mapping.get("host", [])),
            severity_hint=str(_extract(raw, mapping.get("severity", [])) or ""),
            message=_extract(raw, mapping.get("message", [])),
            src_port=_extract(raw, mapping.get("src_port", [])),
            dst_port=_extract(raw, mapping.get("dst_port", [])),
            event_type=_classify_event(raw, mapping),
            raw_json=raw,
            extras=extras,
        )
        events.append(evt)

    return events
