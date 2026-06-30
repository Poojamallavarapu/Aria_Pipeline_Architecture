# baseline_compare.py
"""
Quick comparison: vector-only vs BM25-only vs hybrid, scored once each
on a fixed question, for an honest baseline row in the ablation table.
"""

from src.retrieval.vector import retrieve as vector_search
from src.retrieval.bm25 import bm25_search
from src.retrieval.fusion import hybrid_retrieve
from src.generation.generator import build_context, build_prompt_qa, MODEL_NAME
from src.evaluation.evaluator import evaluate_answer
import ollama

QUESTION = "What is A01 Broken Access Control?"


def generate_from_chunks(question, chunks):
    context = build_context(chunks)
    prompt = build_prompt_qa(question, context, retry=False)
    response = ollama.chat(model=MODEL_NAME, messages=[{"role": "user", "content": prompt}], options={"temperature": 0.0})
    return response["message"]["content"]


def run_variant(name, chunks):
    answer = generate_from_chunks(QUESTION, chunks)
    contexts = [c["text"] for c in chunks]
    result = evaluate_answer(QUESTION, answer, contexts)
    print(f"\n[{name}] faithfulness={result['faithfulness']:.2f} relevancy={result['answer_relevancy']:.2f} precision={result['context_precision']:.2f}")
    return result


if __name__ == "__main__":
    vector_chunks = vector_search(QUESTION, top_k=5)
    run_variant("vector-only", vector_chunks)

    bm25_chunks = bm25_search(QUESTION, top_k=5)
    run_variant("bm25-only", bm25_chunks)

    hybrid_chunks = hybrid_retrieve(QUESTION, top_k=5, fetch_k=10)
    run_variant("hybrid (no rerank)", hybrid_chunks)