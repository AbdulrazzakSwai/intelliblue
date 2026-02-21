"""
Chat orchestrator with RAG-like retrieval.
"""
import uuid
from pathlib import Path
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .runtime import generate, get_model_name
from ..retrieval.keyword_search import search_incidents, search_events
from ..retrieval.context_builder import build_context
from ..models.chat import ChatSession, ChatMessage, MessageRole


PROMPT_VERSION = "chat_v1"
PROMPT_PATH = Path(__file__).parent / "prompts" / "chat_v1.txt"


def _load_prompt() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text()
    return "Context: {context}\nQuestion: {question}\nAnswer:"


async def chat_response(
    db: AsyncSession,
    session_id: str,
    question: str,
    dataset_id: Optional[str] = None,
    incident_id: Optional[str] = None,
) -> ChatMessage:
    """Generate a chat response using RAG-like retrieval."""
    # Retrieve relevant context
    incidents = await search_incidents(db, question, dataset_id=dataset_id, incident_id=incident_id)
    events = await search_events(db, question, dataset_id=dataset_id)
    context, evidence_refs = build_context(incidents, events)

    model_name = get_model_name()

    if not context:
        context = "No relevant incidents or events found in the database for this query."

    prompt_template = _load_prompt()
    prompt = prompt_template.format(context=context, question=question)

    raw_output = generate(prompt)

    if raw_output:
        content = raw_output
    else:
        content = (
            "LLM is not configured. To enable AI responses, download a GGUF model file "
            "and set LLM_MODEL_PATH in your .env file. "
            f"Found {len(incidents)} incident(s) and {len(events)} event(s) related to your query."
        )

    msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=str(session_id),
        role=MessageRole.ASSISTANT,
        content=content,
        evidence_refs=evidence_refs,
        model_name=model_name,
        prompt_version=PROMPT_VERSION,
    )
    db.add(msg)
    await db.flush()
    return msg
