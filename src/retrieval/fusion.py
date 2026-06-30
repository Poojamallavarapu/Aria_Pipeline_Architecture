"""
fusion.py
Reciprocal Rank Fusion (RRF) combining vector and BM25 results.
"""

from src.retrieval.vector import retrieve as vector_search
from src.retrieval.bm25 import bm25_search


def rrf_fusion(vector_results, bm25_results, k=60, top_k=5):
    """
    Combine two ranked result lists using Reciprocal Rank Fusion.

    k is the RRF constant (60 is standard).
    Dedup is done on metadata['chunk_id'].
    """
    scores = {}

    for rank, r in enumerate(vector_results):
        chunk_id = r["metadata"]["chunk_id"]
        if chunk_id not in scores:
            scores[chunk_id] = {"score": 0.0, "data": r}
        scores[chunk_id]["score"] += 1 / (k + rank + 1)

    for rank, r in enumerate(bm25_results):
        chunk_id = r["metadata"]["chunk_id"]
        if chunk_id not in scores:
            scores[chunk_id] = {"score": 0.0, "data": r}
        scores[chunk_id]["score"] += 1 / (k + rank + 1)

    ranked = sorted(scores.values(), key=lambda x: x["score"], reverse=True)[:top_k]
    return [r["data"] for r in ranked]


def hybrid_retrieve(query: str, top_k: int = 5, fetch_k: int = 10):
    """
    Run vector + BM25 retrieval and fuse results with RRF.

    fetch_k: how many results to fetch from EACH retriever before fusion
             (should be >= top_k to give fusion enough candidates)
    """
    vector_results = vector_search(query, top_k=fetch_k)
    bm25_results = bm25_search(query, top_k=fetch_k)

    fused = rrf_fusion(vector_results, bm25_results, top_k=top_k)
    return fused


if __name__ == "__main__":
    query = input("Query: ")
    results = hybrid_retrieve(query)

    print("\n===== HYBRID (RRF) RESULTS =====")
    for r in results:
        print()
        print(r["metadata"])
        print(r["text"][:300])