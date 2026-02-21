"""
Local LLM runtime using llama-cpp-python.
CPU-first with optional GPU layers. Gracefully degrades if model not found.
"""
import logging
from pathlib import Path
from typing import Optional
from ..config import settings

logger = logging.getLogger(__name__)

_llm = None
_llm_loaded = False
_model_name = None


def get_llm():
    """Get the LLM instance, loading it if needed. Returns None if unavailable."""
    global _llm, _llm_loaded, _model_name

    if _llm_loaded:
        return _llm

    _llm_loaded = True
    model_path = Path(settings.llm_model_path)

    if not model_path.exists():
        logger.warning(f"LLM model not found at {model_path}. LLM features disabled.")
        return None

    try:
        from llama_cpp import Llama
        _llm = Llama(
            model_path=str(model_path),
            n_gpu_layers=settings.llm_n_gpu_layers,
            n_ctx=settings.llm_n_ctx,
            verbose=False,
        )
        _model_name = model_path.name
        logger.info(f"LLM loaded: {_model_name}")
        return _llm
    except ImportError:
        logger.warning("llama-cpp-python not installed. LLM features disabled.")
        return None
    except Exception as e:
        logger.error(f"Failed to load LLM: {e}")
        return None


def get_model_name() -> Optional[str]:
    return _model_name


def generate(prompt: str, max_tokens: int = None) -> Optional[str]:
    """Generate text from a prompt. Returns None if LLM unavailable."""
    llm = get_llm()
    if llm is None:
        return None
    try:
        result = llm(
            prompt,
            max_tokens=max_tokens or settings.llm_max_tokens,
            temperature=0.1,
            stop=["</s>", "[INST]"],
        )
        return result["choices"][0]["text"].strip()
    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        return None
