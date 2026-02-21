# LLM Setup Guide

IntelliBlue uses `llama-cpp-python` for local LLM inference. The system works fully without an LLM — AI summaries and chat responses show a "LLM not configured" message.

## Supported Model Format

GGUF format models (quantized). Any GGUF model compatible with llama-cpp-python.

## Recommended Models

| Model | Size | Notes |
|-------|------|-------|
| Phi-3-mini-4k-instruct-Q4_K_M | ~2.2GB | Best quality/size for CPU |
| Llama-3.2-3B-Instruct-Q4_K_M | ~1.9GB | Faster on slow hardware |
| Mistral-7B-Instruct-v0.2-Q4_K_M | ~4.4GB | Best reasoning, needs more RAM |

## Download (requires internet)

```bash
# Using huggingface-cli
pip install huggingface_hub
huggingface-cli download microsoft/Phi-3-mini-4k-instruct-gguf \
  Phi-3-mini-4k-instruct-q4.gguf --local-dir ./models/
```

## Configuration

In `.env`:
```
LLM_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
LLM_N_GPU_LAYERS=0    # 0 = CPU only, -1 = all layers on GPU
LLM_N_CTX=4096        # Context window (reduce if low RAM)
LLM_MAX_TOKENS=1024   # Max tokens in response
```

## GPU Acceleration (Optional)

Install with CUDA support:
```bash
CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python
```

Then set `LLM_N_GPU_LAYERS=-1` or a positive number of layers.

## Graceful Degradation

If `LLM_MODEL_PATH` is not set or the file doesn't exist, the backend starts normally. The `/incidents/{id}/summarize` endpoint returns a message indicating LLM is unavailable. Chat responses include a helpful fallback message.
