"""
Incident summarization orchestrator.
"""
import json
import time
import uuid
from pathlib import Path
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .runtime import generate, get_model_name
from ..models.incident import Incident
from ..models.event import Event
from ..models.incident_event import IncidentEvent
from ..models.incident_ai_summary import IncidentAISummary


PROMPT_VERSION = "summarizer_v1"
PROMPT_PATH = Path(__file__).parent / "prompts" / "summarizer_v1.txt"


def _load_prompt() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text()
    return "Summarize this incident: {incident_context}\nEvidence: {evidence_snippets}\nEntities: {entities}\nTimeline: {timeline}"


async def summarize_incident(db: AsyncSession, incident_id: str) -> Optional[IncidentAISummary]:
    """Generate an AI summary for an incident."""
    incident = await db.get(Incident, str(incident_id))
    if not incident:
        return None

    # Get linked events
    result = await db.execute(
        select(Event)
        .join(IncidentEvent, IncidentEvent.event_id == Event.id)
        .where(IncidentEvent.incident_id == incident_id)
        .limit(20)
    )
    events = result.scalars().all()

    entities = {}
    timeline_lines = []
    evidence_snippets = []

    for ev in events:
        if ev.src_ip:
            entities.setdefault("src_ips", set()).add(ev.src_ip)
        if ev.username:
            entities.setdefault("users", set()).add(ev.username)
        if ev.event_time:
            timeline_lines.append(f"{ev.event_time.isoformat()} [{ev.source_type}] {ev.event_type}: {ev.src_ip or ''} {ev.message or ''}")
        evidence_snippets.append(f"[{ev.source_type}] {ev.event_type}: src={ev.src_ip} user={ev.username} msg={ev.message}")

    entities_serializable = {k: list(v) for k, v in entities.items()}
    incident_context = (
        f"Title: {incident.title}\n"
        f"Severity: {incident.severity}\n"
        f"Type: {incident.incident_type}\n"
        f"Rule: {incident.rule_explanation}\n"
    )

    prompt_template = _load_prompt()
    prompt = prompt_template.format(
        incident_context=incident_context,
        evidence_snippets="\n".join(evidence_snippets[:10]),
        entities=json.dumps(entities_serializable),
        timeline="\n".join(sorted(timeline_lines)[:15]),
    )

    model_name = get_model_name()
    start = time.time()
    raw_output = generate(prompt)
    elapsed = time.time() - start

    summary_json = None
    narrative = None

    if raw_output:
        try:
            # Extract JSON from output
            start_idx = raw_output.find("{")
            end_idx = raw_output.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                summary_json = json.loads(raw_output[start_idx:end_idx])
                narrative = summary_json.get("summary")
        except (json.JSONDecodeError, ValueError):
            narrative = raw_output

    ai_summary = IncidentAISummary(
        id=str(uuid.uuid4()),
        incident_id=incident_id,
        summary_json=summary_json,
        narrative=narrative,
        model_name=model_name,
        prompt_version=PROMPT_VERSION,
        generation_time_sec=elapsed if raw_output else None,
    )
    db.add(ai_summary)
    await db.flush()
    return ai_summary
