"""
bm25.py
BM25 retrieval with disk-cached index to avoid rebuilding on every query.
"""

import pickle
from pathlib import Path
from rank_bm25 import BM25Okapi

BM25_CACHE = "bm25_index.pkl"


def build_bm25_index(chunks: list[dict]) -> None:
    """
    Build BM25 index from chunks and cache it to disk.
    Run this once after embedding (or whenever documents change).
    """
    tokenized = [c["text"].lower().split() for c in chunks]
    bm25 = BM25Okapi(tokenized)

    with open(BM25_CACHE, "wb") as f:
        pickle.dump({"bm25": bm25, "chunks": chunks}, f)

    print(f"BM25 index built and cached: {len(chunks)} chunks -> {BM25_CACHE}")


def load_bm25_index():
    """Load cached BM25 index from disk."""
    if not Path(BM25_CACHE).exists():
        raise FileNotFoundError(
            f"{BM25_CACHE} not found. Run 'python build_bm25.py' first."
        )

    with open(BM25_CACHE, "rb") as f:
        data = pickle.load(f)

    return data["bm25"], data["chunks"]


def bm25_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Search the cached BM25 index for the top_k most relevant chunks.

    Returns:
    [{"text": ..., "metadata": {...}, "score": float}, ...]
    """
    bm25, chunks = load_bm25_index()

    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    ranked = sorted(
        zip(scores, chunks), key=lambda x: x[0], reverse=True
    )[:top_k]

    return [
        {"text": c["text"], "metadata": c["metadata"], "score": float(s)}
        for s, c in ranked
    ]


if __name__ == "__main__":
    query = input("Query: ")
    results = bm25_search(query)

    print("\n===== BM25 RESULTS =====")
    for r in results:
        print(f"\nScore: {r['score']:.4f}")
        print(r["metadata"])
        print(r["text"][:300])