# =============================================================
#  ARIA – Self-healing Cybersecurity RAG Assistant
#  Multi-stage Dockerfile  (FastAPI + Streamlit + Ollama)
#  Optimised for Hugging Face Docker Spaces (port 7860, UID 1000)
# =============================================================

# ---------- Stage 1: Build / install Python deps ----------
FROM python:3.11-slim AS builder

WORKDIR /build

# System libs needed by some Python packages (numpy, PyMuPDF, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ pkg-config \
    libsndfile1 libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install to a prefix so we can COPY cleanly into the runtime stage.
# --extra-index-url in requirements.txt pulls CPU-only PyTorch (~200 MB)
# instead of the default CUDA build (~2.5 GB).
RUN python -m pip install --upgrade pip wheel \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Stage 2: Runtime image ----------
FROM python:3.11-slim

LABEL maintainer="pooja"
LABEL description="ARIA – Self-healing Cybersecurity RAG Assistant"

# ── Create non-root user required by Hugging Face Spaces ──
# HF Spaces runs containers as UID 1000 and refuses root.
RUN useradd -m -u 1000 -s /bin/bash user

# ── Environment variables ──
ENV PYTHONUNBUFFERED=1 \
    # Python path must point to the app root so imports resolve correctly
    PYTHONPATH=/home/user/app \
    # Ollama must write models to the user's home, not /root
    OLLAMA_MODELS=/home/user/.ollama/models \
    HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /home/user/app

# ── Runtime system deps ──
# curl/wget: Ollama installer + health probes
# libsndfile1, libgl1, libglib2.0-0: required by sentence-transformers / PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget zstd libsndfile1 libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ── Install Ollama ──
# The installer writes to /usr/local/bin/ollama and /usr/lib/ollama.
# We install as root so the binary is system-wide, but Ollama's model
# *data* will go to OLLAMA_MODELS which points to the user's home.
RUN curl -fsSL https://ollama.com/install.sh | sh

# ── Create writable directories owned by user 1000 ──
# - .ollama:        where Ollama stores downloaded model weights
# - chroma_db:      where ChromaDB persists vector embeddings
# - app root:       where healing_memory.json and bm25_index.pkl are written
RUN mkdir -p /home/user/.ollama/models \
    && chown -R user:user /home/user/.ollama \
    && chown -R user:user /home/user/app

# ── Copy pre-built Python packages from builder stage ──
COPY --from=builder /install /usr/local

# ── Copy application source code (owned by user 1000) ──
COPY --chown=user:user api/          ./api/
COPY --chown=user:user src/          ./src/
COPY --chown=user:user frontend/     ./frontend/
COPY --chown=user:user data/         ./data/
COPY --chown=user:user scripts/      ./scripts/
COPY --chown=user:user build_bm25.py .
COPY --chown=user:user start.sh      .

# ── Copy pre-built ChromaDB index (avoids re-embedding on cold start) ──
COPY --chown=user:user chroma_db/    ./chroma_db/

# ── Make startup script executable ──
RUN chmod +x start.sh

# ── Switch to non-root user for all runtime operations ──
USER user

# ── Expose ports ──
# 7860 = Streamlit frontend  (Hugging Face Spaces requirement)
# 8000 = FastAPI backend
EXPOSE 7860 8000

# ── Launch everything via startup script ──
CMD ["bash", "./start.sh"]