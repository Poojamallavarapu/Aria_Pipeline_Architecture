

# ARIA – Adaptive Retrieval Intelligence Architecture

ARIA is a production-grade, self-healing cybersecurity RAG assistant designed for high-stakes document Q&A. It operates over complex regulations and frameworks (such as NIST CSF 2.0, OWASP Top 10, MITRE ATT&CK) with $0 API cost using local open-source models.

## Key Features

- **Hybrid Retrieval (RRF)**: Merges keyword (BM25) and semantic vector search (ChromaDB) rankings.
- **Cross-Encoder Reranking**: Utilizes `cross-encoder/ms-marco-MiniLM-L-12-v2` to surface the most context-relevant chunks.
- **Answer Evaluation (RAGAS)**: Real-time, per-query evaluation scoring across faithfulness, answer relevancy, and context precision.
- **Agentic Self-Healing Engine**: Automatically diagnoses score failures and dynamically applies targeted healing strategies (Query Rewriting, Retrieval Expansion + MMR, Query Decomposition) to fix answers.
- **Langfuse Tracing**: Full end-to-end tracing of the pipeline layers (retrieval, generation, evaluation, healing loops).

