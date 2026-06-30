#!/bin/bash
# =============================================================
#  ARIA startup script
#  Compatible with: bash 4.x+, python:3.11-slim
#  Runs as: non-root user (UID 1000)
# =============================================================

# Exit immediately on any unhandled error, treat unset variables
# as errors, and propagate pipe failures correctly.
set -euo pipefail

APP_DIR="/home/user/app"

echo "============================================"
echo "  ARIA – Starting all services..."
echo "============================================"

# --------------------------------------------------
# 1. Start Ollama in the background
# --------------------------------------------------
echo "[1/4] Starting Ollama server..."

# OLLAMA_MODELS is set in the Dockerfile ENV so Ollama writes
# model weights to /home/user/.ollama/models (not /root).
ollama serve &
OLLAMA_PID=$!

# Wait until Ollama is accepting connections (up to 240 seconds)
echo "       Waiting for Ollama to be ready..."
READY=0
for i in $(seq 1 120); do
    if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "       Ollama is ready (attempt $i)."
        READY=1
        break
    fi
    sleep 2
done

if [ "$READY" -eq 0 ]; then
    echo "ERROR: Ollama did not become ready after 240 seconds. Aborting."
    exit 1
fi

# --------------------------------------------------
# 2. Pull required models (skip if already cached)
# --------------------------------------------------
echo "[2/4] Pulling LLM models (will skip if already cached)..."
ollama pull llama3.1:8b      || echo "  WARNING: Could not pull llama3.1:8b – queries will fail."
ollama pull nomic-embed-text || echo "  WARNING: Could not pull nomic-embed-text – embeddings will fail."

# --------------------------------------------------
# 3. Build BM25 index (only if missing)
# --------------------------------------------------
# Run from the app directory so the relative path in bm25.py
# (BM25_CACHE = "bm25_index.pkl") resolves to the correct location.
cd "$APP_DIR"

if [ ! -f "bm25_index.pkl" ]; then
    echo "[3/4] Building BM25 index..."
    python build_bm25.py
else
    echo "[3/4] BM25 index already exists, skipping build."
fi

# --------------------------------------------------
# 4. Start FastAPI + Streamlit
# --------------------------------------------------
echo "[4/4] Launching FastAPI (port 8000) and Streamlit (port 7860)..."

uvicorn api.main:app --host 0.0.0.0 --port 8000 &
FASTAPI_PID=$!

streamlit run frontend/app.py \
    --server.port 7860 \
    --server.address 0.0.0.0 \
    --server.headless true &
STREAMLIT_PID=$!

echo "============================================"
echo "  ARIA is running!"
echo "  API:       http://localhost:8000"
echo "  Frontend:  http://localhost:7860"
echo "============================================"

# Keep container alive.
# Use individual waits (compatible with bash 4.x).
# 'wait -n' is bash 5.1+ and is NOT available in python:3.11-slim.
# If any one of the three processes exits, the container exits.
wait $OLLAMA_PID $FASTAPI_PID $STREAMLIT_PID