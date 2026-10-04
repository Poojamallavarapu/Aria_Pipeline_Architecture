---
title: ARIA – Self-Healing Cybersecurity RAG
emoji: 🛡️
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

<h1 align="center">🛡️ ARIA – Adaptive Retrieval Intelligence Architecture</h1>

<p align="center">
  <b>A production-grade, self-healing RAG assistant built for cybersecurity document intelligence.</b><br/>
  Operates entirely on local open-source models with <b>$0 API cost</b>.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python"/>
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker"/>
  <img src="https://img.shields.io/badge/LLM-Ollama-black?style=flat-square"/>
  <img src="https://img.shields.io/badge/Vector%20DB-ChromaDB-orange?style=flat-square"/>
  <img src="https://img.shields.io/badge/License-Proprietary-red?style=flat-square"/>
</p>

---

## 📌 Overview

**ARIA** is a self-healing Retrieval-Augmented Generation (RAG) system purpose-built for **high-stakes cybersecurity document Q&A**. It processes complex regulatory and threat frameworks — such as **NIST CSF 2.0**, **OWASP Top 10**, and **MITRE ATT&CK** — and answers questions with measurable confidence, zero cloud API dependency, and a built-in self-correction loop.

Unlike standard RAG systems, ARIA doesn't just retrieve and answer — it **evaluates its own responses** in real time and **autonomously heals poor-quality answers** before returning them to the user.

---

## 🚀 Key Capabilities

### 🔍 Hybrid Retrieval with Reciprocal Rank Fusion (RRF)
ARIA combines two complementary retrieval strategies:
- **BM25** – keyword-based sparse retrieval for exact term matching
- **ChromaDB** – semantic vector search using dense embeddings

Both rankings are fused using **Reciprocal Rank Fusion (RRF)**, producing a retrieval result that is more robust than either method alone.

### 🎯 Cross-Encoder Reranking
Retrieved document chunks are re-ranked using a **cross-encoder model** (`ms-marco-MiniLM-L-12-v2`) to ensure only the most contextually relevant content is passed to the LLM.

### 📊 Real-Time Answer Evaluation (RAGAS)
Every answer is scored across three dimensions before being shown to the user:
| Metric | What it measures |
|---|---|
| **Faithfulness** | Is the answer grounded in the retrieved context? |
| **Answer Relevancy** | Does the answer actually address the question? |
| **Context Precision** | Was the right context retrieved? |

### 🔄 Agentic Self-Healing Engine
This is ARIA's core differentiator. When evaluation scores fall below acceptable thresholds, ARIA's **autonomous healing engine** kicks in and applies one or more of the following strategies:

| Strategy | What it does |
|---|---|
| **Query Rewriting** | Rephrases the original question for better retrieval |
| **Retrieval Expansion + MMR** | Fetches more diverse documents using Maximal Marginal Relevance |
| **Query Decomposition** | Breaks complex questions into focused sub-queries |

The engine tracks healing history in persistent memory, learns from past failures, and avoids repeating unsuccessful strategies.

### 🔭 Full Observability with Langfuse
End-to-end tracing of every pipeline layer — retrieval, generation, evaluation, and healing — through **Langfuse**, providing full auditability of every decision ARIA makes.

---

## 🏗️ System Architecture

```
User Query
    │
    ▼
┌──────────────────────────────────────────────┐
│               ARIA Pipeline                  │
│                                              │
│  [Hybrid Retrieval]  BM25 + ChromaDB + RRF  │
│         │                                    │
│  [Reranking]  Cross-Encoder Reranker        │
│         │                                    │
│  [Generation]  Ollama LLM (local)           │
│         │                                    │
│  [Evaluation]  RAGAS Scoring Engine         │
│         │                                    │
│  [Self-Healing]  Agentic Healing Engine     │
│         │                                    │
│  [Observability]  Langfuse Tracing          │
└──────────────────────────────────────────────┘
    │
    ▼
Final Answer + Confidence Score + Metrics
```

---

## 🧱 Technology Stack

| Layer | Technology |
|---|---|
| LLM Backend | [Ollama](https://ollama.com/) (fully local) |
| Vector Database | [ChromaDB](https://www.trychroma.com/) |
| Sparse Retrieval | BM25 (`rank-bm25`) |
| Embeddings | `sentence-transformers` |
| Reranking | `cross-encoder/ms-marco-MiniLM-L-12-v2` |
| Evaluation | [RAGAS](https://docs.ragas.io/) |
| Orchestration | [LangChain](https://www.langchain.com/) |
| API | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Observability | [Langfuse](https://langfuse.com/) |
| Containerization | Docker (multi-stage build) |

---

## 📁 Project Structure

```
Aria/
├── api/                    # FastAPI backend
├── src/
│   ├── ingestion/          # Document loading & chunking
│   ├── retrieval/          # Hybrid retrieval (BM25 + vector)
│   ├── generation/         # LLM answer generation
│   ├── evaluation/         # RAGAS scoring
│   ├── healing/            # Self-healing engine & strategies
│   ├── observability/      # Langfuse tracing
│   └── pipeline.py         # Main pipeline entry point
├── frontend/               # Streamlit UI
├── data/                   # Cybersecurity documents
├── chroma_db/              # Persisted vector index
├── Dockerfile              # Multi-stage Docker build (HF Spaces compatible)
├── docker-compose.yml      # Local orchestration
├── start.sh                # Container startup script
└── requirements.txt        # Python dependencies
```

---

## 🖥️ Running Locally

### Prerequisites
- [Docker](https://www.docker.com/) installed
- `.env` file with required environment variables (see `.env.example`)

### Build & Run
```bash
docker build -t aria-hf .
docker run -p 7860:7860 -p 8000:8000 --env-file .env aria-hf
```

Open **http://localhost:7860** in your browser.

---

## 🌐 Live Demo

Deployed on Hugging Face Spaces using Docker SDK.  
The app exposes:
- **Port 7860** → Streamlit frontend (chat interface)
- **Port 8000** → FastAPI backend (REST API)

---

## ⚠️ Important Notice

> **This project and all its source code, architecture design, self-healing pipeline logic, and evaluation methodology are the original intellectual work of [Pooja Mallavarapu](https://github.com/Poojamallavarapu).**
>
> This repository is made **publicly visible for portfolio and demonstration purposes only**.
>
> ❌ **You may NOT** copy, reproduce, redistribute, or use any part of this codebase — in whole or in part — for commercial or academic purposes without explicit written permission from the author.
>
> ❌ **You may NOT** claim this work or any derived version of it as your own.
>
> ✅ You are welcome to **read, learn from, and reference** this project with proper attribution.
>
> For collaboration or licensing inquiries, please reach out via GitHub.

---

## 📄 License

**All Rights Reserved © 2025 Pooja Mallavarapu**

This is proprietary software. No open-source license is granted. See the notice above for terms of use.

---

<p align="center">Built with 🧠 by <a href="https://github.com/Poojamallavarapu">Pooja Mallavarapu</a></p>
