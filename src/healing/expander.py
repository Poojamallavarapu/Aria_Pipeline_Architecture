"""
expander.py
Strategy B: Expansion + MMR.
Triggered when faithfulness is low — the topic is right but there's
insufficient evidence to ground a faithful answer. Expand retrieval
and diversify chunks via MMR.
"""

import logging
import numpy as np

from src.retrieval.fusion import hybrid_retrieve
from src.retrieval.reranker import rerank
from src.ingestion.embedder import get_embedding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _cosine_sim(a: list[float], b: list[float]) -> float:
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def mmr_select(query: str, candidates: list[dict], top_k: int = 10, lambda_param: float = 0.7) -> list[dict]:
    """
    Maximal Marginal Relevance: selects chunks that are relevant to the
    query AND diverse from each other (reduces redundant near-duplicate
    chunks that all say the same thing).
    """
    if len(candidates) <= top_k:
        return candidates

    query_emb = get_embedding(query)

    chunk_embs = [get_embedding(c["text"]) for c in candidates]

    selected_idx = []
    remaining_idx = list(range(len(candidates)))

    # Pick the most relevant chunk first
    rel_scores = [_cosine_sim(query_emb, emb) for emb in chunk_embs]
    first = max(remaining_idx, key=lambda i: rel_scores[i])
    selected_idx.append(first)
    remaining_idx.remove(first)

    while len(selected_idx) < top_k and remaining_idx:
        mmr_scores = []
        for i in remaining_idx:
            relevance = rel_scores[i]
            max_sim_to_selected = max(
                _cosine_sim(chunk_embs[i], chunk_embs[j]) for j in selected_idx
            )
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected
            mmr_scores.append((i, mmr_score))

        best_i, _ = max(mmr_scores, key=lambda x: x[1])
        selected_idx.append(best_i)
        remaining_idx.remove(best_i)

    return [candidates[i] for i in selected_idx]


def expand_retrieval(query: str, expanded_top_k: int = 10) -> list[dict]:
    """
    Expand retrieval from default top_k to a larger pool, then apply MMR
    to select a diverse, relevant subset.
    """
    candidates = hybrid_retrieve(query, top_k=expanded_top_k * 2, fetch_k=expanded_top_k * 3)
    reranked = rerank(query, candidates, top_k=expanded_top_k)

    diversified = mmr_select(query, reranked, top_k=expanded_top_k)

    logger.info(f"Expanded retrieval: {len(diversified)} diversified chunks")

    return diversified


if __name__ == "__main__":
    query = input("Query: ")
    results = expand_retrieval(query)

    print(f"\n===== EXPANDED + MMR RESULTS ({len(results)} chunks) =====")
    for r in results:
        print(f"\n{r['metadata']}")
        print(r["text"][:200])