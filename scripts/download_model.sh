#!/bin/bash
# Download a GGUF model for local LLM inference
# Run this BEFORE going offline!

MODEL_DIR="./models"
mkdir -p "$MODEL_DIR"

echo "IntelliBlue SOC - LLM Model Downloader"
echo "======================================="
echo ""
echo "Recommended models (small enough for CPU inference):"
echo "1. Phi-3-mini-4k-instruct-q4 (~2.2GB) - Fast, good quality"
echo "2. mistral-7b-instruct-v0.2-q4 (~4.4GB) - Better reasoning"
echo "3. llama-3.2-3b-instruct-q4 (~1.8GB) - Fastest"
echo ""
echo "Download a model from Hugging Face and place it in: $MODEL_DIR"
echo "Then set LLM_MODEL_PATH=./models/your-model.gguf in .env"
echo ""

# Example with huggingface-cli (install with: pip install huggingface_hub)
if command -v huggingface-cli &> /dev/null; then
    echo "huggingface-cli found. You can run:"
    echo "  huggingface-cli download microsoft/Phi-3-mini-4k-instruct-gguf Phi-3-mini-4k-instruct-q4.gguf --local-dir $MODEL_DIR"
fi

echo ""
echo "Or download manually and place in $MODEL_DIR/"
