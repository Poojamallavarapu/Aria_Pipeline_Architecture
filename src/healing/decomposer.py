"""
decomposer.py
Strategy C: Query Decomposition.
"""

import logging
import ollama

from src.retrieval.fusion import hybrid_retrieve
from src.retrieval.reranker import rerank
from src.generation.generator import build_context, build_prompt, MODEL_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DECOMPOSE_OPTIONS = {"temperature": 0.0, "num_predict": 150}


def decompose_query(question: str) -> list[str]:
    prompt = f"""You are a query decomposition assistant for cybersecurity questions.

Break the following question into 2-3 simpler, focused sub-questions that
together would fully answer the original question. If the question is
already simple, return just 1 sub-question (the original, rephrased clearly).

Original question: {question}

Respond with ONLY the sub-questions, one per line, no numbering, no explanation."""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options=DECOMPOSE_OPTIONS,
    )

    sub_questions = [
        line.strip() for line in response["message"]["content"].split("\n")
        if line.strip()
    ]

    logger.info(f"Decomposed into {len(sub_questions)} sub-questions: {sub_questions}")
    return sub_questions


def answer_sub_question(sub_question: str) -> str:
    candidates = hybrid_retrieve(sub_question, top_k=10, fetch_k=15)
    chunks = rerank(sub_question, candidates, top_k=3)
    context = build_context(chunks)
    prompt = build_prompt(sub_question, context, retry=False)

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options=DECOMPOSE_OPTIONS,
    )
    return response["message"]["content"]


def synthesize_answers(original_question: str, sub_qa_pairs: list[tuple[str, str]]) -> str:
    qa_text = "\n\n".join(
        f"Sub-question: {q}\nAnswer: {a}" for q, a in sub_qa_pairs
    )

    prompt = f"""You are synthesizing a final answer from sub-question answers.

Original question: {original_question}

{qa_text}

Combine the above into one clear, coherent answer to the original question.
Use ONLY information from the sub-answers above. Cite sources mentioned in the sub-answers."""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options=DECOMPOSE_OPTIONS,
    )
    return response["message"]["content"]


def decompose_and_answer(question: str) -> str:
    sub_questions = decompose_query(question)
    sub_qa_pairs = []
    for sub_q in sub_questions:
        sub_answer = answer_sub_question(sub_q)
        sub_qa_pairs.append((sub_q, sub_answer))
    return synthesize_answers(question, sub_qa_pairs)


if __name__ == "__main__":
    question = input("Question: ")
    answer = decompose_and_answer(question)
    print(f"\n===== SYNTHESIZED ANSWER =====")
    print(answer)