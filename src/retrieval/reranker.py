"""
reranker.py
Cross-encoder reranking of retrieved chunks.
"""

MIN_CHUNK_LENGTH = 100  # characters

def rerank(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    """
    Rerank candidate chunks using a cross-encoder.
    Filters out chunks below MIN_CHUNK_LENGTH before scoring.
    """
    # Filter short chunks first (Section 9 failure analysis fix)
    filtered = [r for r in results if len(r["text"]) >= MIN_CHUNK_LENGTH]

    # Fallback: if filtering removes everything, use original results
    if not filtered:
        filtered = results

    model = get_model()

    pairs = [(query, r["text"]) for r in filtered]
    scores = model.predict(pairs)

    for r, score in zip(filtered, scores):
        r["rerank_score"] = float(score)

    reranked = sorted(filtered, key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_k]

import logging
from sentence_transformers import CrossEncoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_model = None


def get_model():
    """Lazy-load the cross-encoder model (loaded once, reused)."""
    global _model
    if _model is None:
        logger.info(f"Loading reranker model: {RERANKER_MODEL}")
        _model = CrossEncoder(RERANKER_MODEL)
    return _model


def rerank(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    """
    Rerank candidate chunks using a cross-encoder.

    results: list of {"text": ..., "metadata": ...}
    Returns top_k results sorted by cross-encoder relevance score.
    """
    model = get_model()

    pairs = [(query, r["text"]) for r in results]
    scores = model.predict(pairs)

    for r, score in zip(results, scores):
        r["rerank_score"] = float(score)

    reranked = sorted(results, key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_k]


if __name__ == "__main__":
    from src.retrieval.fusion import hybrid_retrieve

    query = input("Query: ")

    candidates = hybrid_retrieve(query, top_k=10, fetch_k=15)
    reranked = rerank(query, candidates, top_k=5)

    print("\n===== RERANKED RESULTS =====")
    for r in reranked:
        print(f"\nRerank Score: {r['rerank_score']:.4f}")
        print(r["metadata"])
        print(r["text"][:300])