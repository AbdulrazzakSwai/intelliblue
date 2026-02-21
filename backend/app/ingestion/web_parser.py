import re
from datetime import datetime, timezone
from typing import List, Optional
from .normalizer import NormalizedEvent

# Apache/Nginx Combined Log Format
# 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.1" 200 2326 "http://ref.example.com/" "Mozilla/4.08"
COMBINED_LOG_RE = re.compile(
    r'(?P<src_ip>\S+)'           # IP
    r'\s+\S+'                    # ident
    r'\s+(?P<user>\S+)'          # user
    r'\s+\[(?P<time>[^\]]+)\]'   # time
    r'\s+"(?P<request>[^"]*)"'   # request
    r'\s+(?P<status>\d+)'        # status
    r'\s+(?P<size>\S+)'          # size
    r'(?:\s+"(?P<referer>[^"]*)")?' 
    r'(?:\s+"(?P<user_agent>[^"]*)")?'
)

SUSPICIOUS_UA = [
    "nikto", "sqlmap", "nmap", "dirbuster", "gobuster", "masscan",
    "zgrab", "nuclei", "wfuzz", "dirb", "hydra", "metasploit",
    "python-requests", "curl", "wget",
]

TIME_FMT = "%d/%b/%Y:%H:%M:%S %z"


def _parse_web_time(val: str) -> Optional[datetime]:
    try:
        return datetime.strptime(val, TIME_FMT)
    except ValueError:
        return None


def _classify_web_event(status: int, ua: str) -> str:
    ua_lower = ua.lower()
    if any(s in ua_lower for s in SUSPICIOUS_UA):
        return "suspicious_ua"
    if status == 401:
        return "web_401"
    if status == 403:
        return "web_403"
    if status == 404:
        return "web_404"
    if 400 <= status < 500:
        return "web_4xx"
    if 200 <= status < 300:
        return "web_request"
    return "web_request"


def parse_web_log(content: str) -> List[NormalizedEvent]:
    """Parse Apache/Nginx Combined Log Format."""
    events: List[NormalizedEvent] = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        m = COMBINED_LOG_RE.match(line)
        if not m:
            continue
        src_ip = m.group("src_ip")
        user = m.group("user")
        if user == "-":
            user = None
        time_str = m.group("time")
        request = m.group("request")
        status_str = m.group("status")
        size_str = m.group("size")
        ua = m.group("user_agent") or ""

        method, url_path, protocol = None, None, None
        if request:
            parts = request.split(" ", 2)
            if len(parts) >= 2:
                method = parts[0]
                url_path = parts[1]
            if len(parts) == 3:
                protocol = parts[2]

        try:
            status = int(status_str)
        except (TypeError, ValueError):
            status = 0
        try:
            size = int(size_str) if size_str and size_str != "-" else None
        except ValueError:
            size = None

        evt = NormalizedEvent(
            source_type="WEB_LOG",
            event_time=_parse_web_time(time_str),
            src_ip=src_ip,
            username=user,
            http_method=method,
            url_path=url_path,
            http_status=status,
            response_size=size,
            user_agent=ua,
            protocol=protocol,
            event_type=_classify_web_event(status, ua),
            raw_json={"line": line},
        )
        events.append(evt)
    return events
