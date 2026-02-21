import pytest
from datetime import datetime, timezone
from app.ingestion.siem_parser import parse_siem_json
from app.ingestion.web_parser import parse_web_log
from app.ingestion.ids_parser import parse_suricata, parse_snort

pytestmark = pytest.mark.asyncio


SIEM_NDJSON = """\
{"timestamp": "2024-01-15T10:00:00Z", "user": "alice", "src_ip": "192.168.1.100", "action": "login_failure", "host": "dc01"}
{"timestamp": "2024-01-15T10:00:30Z", "user": "alice", "src_ip": "192.168.1.100", "action": "login_failure", "host": "dc01"}
{"timestamp": "2024-01-15T10:01:00Z", "user": "bob", "src_ip": "10.0.0.50", "action": "login_success", "host": "ws01"}
"""

SIEM_JSON_ARRAY = """\
[
  {"timestamp": "2024-01-15T10:00:00Z", "user": "alice", "action": "login_failure"},
  {"timestamp": "2024-01-15T10:01:00Z", "user": "bob", "action": "login_success"}
]
"""

WEB_LOG = """\
192.168.1.200 - - [15/Jan/2024:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 1234 "-" "Mozilla/5.0"
192.168.1.200 - - [15/Jan/2024:10:00:01 +0000] "GET /admin HTTP/1.1" 404 512 "-" "Nikto/2.1.6"
10.0.0.1 - frank [15/Jan/2024:10:00:02 +0000] "GET /login HTTP/1.1" 401 256 "-" "Mozilla/5.0 (Windows NT 10.0)"
"""

SURICATA_EVE = """\
{"timestamp": "2024-01-15T10:00:00.000000+0000", "event_type": "alert", "src_ip": "192.168.1.100", "dest_ip": "10.0.0.1", "src_port": 4321, "dest_port": 22, "proto": "TCP", "alert": {"signature_id": 2001219, "signature": "ET SCAN Potential SSH Scan", "category": "Attempted Information Leak", "severity": 2}}
{"timestamp": "2024-01-15T10:00:05.000000+0000", "event_type": "flow", "src_ip": "192.168.1.100"}
"""

SNORT_JSON = """\
[
  {"timestamp": "2024-01-15T10:00:00Z", "sid": 1000001, "msg": "Possible Brute Force", "classtype": "attempted-admin", "priority": 2, "src_ip": "192.168.1.100", "dst_ip": "10.0.0.1"},
  {"timestamp": "2024-01-15T10:00:10Z", "sid": 1000002, "msg": "SQL Injection Attempt", "classtype": "web-application-attack", "priority": 1, "src_ip": "10.0.0.5", "dst_ip": "10.0.0.2"}
]
"""


def test_siem_ndjson_parse():
    events = parse_siem_json(SIEM_NDJSON)
    assert len(events) == 3
    assert events[0].username == "alice"
    assert events[0].src_ip == "192.168.1.100"
    assert events[0].event_type == "login_failure"
    assert events[2].event_type == "login_success"
    assert events[0].event_time is not None


def test_siem_json_array_parse():
    events = parse_siem_json(SIEM_JSON_ARRAY)
    assert len(events) == 2
    assert events[0].event_type == "login_failure"
    assert events[1].event_type == "login_success"


def test_web_log_parse():
    events = parse_web_log(WEB_LOG)
    assert len(events) == 3
    assert events[0].src_ip == "192.168.1.200"
    assert events[0].http_status == 200
    assert events[1].event_type == "suspicious_ua"
    assert events[2].http_status == 401
    assert events[2].event_type == "web_401"


def test_web_log_extracts_user():
    events = parse_web_log(WEB_LOG)
    assert events[2].username == "frank"


def test_suricata_parse():
    events = parse_suricata(SURICATA_EVE)
    assert len(events) == 1  # Only alert events
    assert events[0].source_type == "SURICATA"
    assert events[0].signature == "ET SCAN Potential SSH Scan"
    assert events[0].ids_priority == 2
    assert events[0].severity_hint == "HIGH"


def test_snort_parse():
    events = parse_snort(SNORT_JSON)
    assert len(events) == 2
    assert events[0].source_type == "SNORT"
    assert events[0].signature == "Possible Brute Force"
    assert events[1].ids_priority == 1
    assert events[1].severity_hint == "CRITICAL"


def test_siem_unknown_fields_in_extras():
    content = '{"timestamp": "2024-01-15T10:00:00Z", "weird_field": "value123", "action": "alert"}'
    events = parse_siem_json(content)
    assert len(events) == 1
    assert "weird_field" in events[0].extras
