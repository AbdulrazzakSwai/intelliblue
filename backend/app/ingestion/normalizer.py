from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class NormalizedEvent:
    """Normalized representation of a security event from any source."""
    source_type: str  # SIEM_JSON, WEB_LOG, SURICATA, SNORT
    event_time: Optional[datetime] = None
    host: Optional[str] = None
    username: Optional[str] = None
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    event_type: Optional[str] = None
    severity_hint: Optional[str] = None
    http_method: Optional[str] = None
    url_path: Optional[str] = None
    http_status: Optional[int] = None
    user_agent: Optional[str] = None
    response_size: Optional[int] = None
    signature_id: Optional[str] = None
    signature: Optional[str] = None
    category: Optional[str] = None
    ids_priority: Optional[int] = None
    protocol: Optional[str] = None
    message: Optional[str] = None
    raw_json: Optional[Dict[str, Any]] = None
    extras: Optional[Dict[str, Any]] = field(default_factory=dict)
