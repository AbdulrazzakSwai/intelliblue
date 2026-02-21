"""
Context builder for LLM chat engine.
Assembles retrieved incidents and events into a context window.
"""
from typing import List, Optional
from ..models.incident import Incident
from ..models.event import Event


def build_context(
    incidents: List[Incident],
    events: List[Event],
    max_chars: int = 3000,
) -> tuple[str, dict]:
    """Build a context string and evidence_refs dict from retrieved items."""
    parts = []
    evidence_refs = {"incident_ids": [], "event_ids": []}

    for inc in incidents:
        evidence_refs["incident_ids"].append(str(inc.id))
        parts.append(
            f"[INCIDENT {inc.id}] {inc.title} | Severity: {inc.severity} | "
            f"Type: {inc.incident_type} | Confidence: {inc.confidence}%\n"
            f"Rule: {inc.rule_explanation or ''}"
        )

    for ev in events:
        evidence_refs["event_ids"].append(str(ev.id))
        parts.append(
            f"[EVENT {ev.id}] {ev.source_type} | {ev.event_type} | "
            f"src={ev.src_ip} user={ev.username} msg={ev.message or ''} "
            f"time={ev.event_time}"
        )

    context = "\n\n".join(parts)
    if len(context) > max_chars:
        context = context[:max_chars] + "...[truncated]"

    return context, evidence_refs
