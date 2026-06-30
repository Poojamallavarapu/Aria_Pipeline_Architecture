"""
evaluator.py
Per-query evaluation: faithfulness, answer relevancy, context precision.
"""

import re
import logging
import ollama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JUDGE_MODEL = "llama3.1:8b"
JUDGE_OPTIONS = {"temperature": 0.0}

THRESHOLDS = {
    "faithfulness": 0.70,
    "answer_relevancy": 0.70,
    "context_precision": 0.60,
}

WEIGHTS = {
    "faithfulness": 0.40,
    "answer_relevancy": 0.35,
    "context_precision": 0.25,
}


def _extract_score(text: str) -> float:
    match = re.search(r"([01](?:\.\d+)?)", text)
    if match:
        return max(0.0, min(1.0, float(match.group(1))))
    return 0.5


def _judge(prompt: str) -> float:
    response = ollama.chat(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options=JUDGE_OPTIONS,
    )
    return _extract_score(response["message"]["content"])


def score_all_combined(question: str, answer: str, contexts: list[str]) -> dict:
    context_text = "\n\n".join(contexts)
    prompt = f"""Evaluate this RAG system's answer across three dimensions.

QUESTION:
{question}

CONTEXT:
{context_text}

ANSWER:
{answer}

Score each dimension from 0 to 1.

1. FAITHFULNESS: Are all claims in the answer supported by the context?
2. RELEVANCY: Does the answer directly address the question?
3. PRECISION: What proportion of context chunks are relevant?

Respond EXACTLY like this:

FAITHFULNESS: 0.8
RELEVANCY: 0.9
PRECISION: 0.7
"""

    response = ollama.chat(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options=JUDGE_OPTIONS,
    )

    text = response["message"]["content"]

    def extract_labeled(label: str) -> float:
        match = re.search(rf"{label}\s*:?\s*([01](?:\.\d+)?)", text, re.IGNORECASE)
        if match:
            return max(0.0, min(1.0, float(match.group(1))))
        return 0.5

    return {
        "faithfulness": extract_labeled("FAITHFULNESS"),
        "answer_relevancy": extract_labeled("RELEVANCY"),
        "context_precision": extract_labeled("PRECISION"),
    }


def evaluate_answer(question: str, answer: str, contexts: list[str]) -> dict:
    scores = score_all_combined(question, answer, contexts)
    faithfulness = scores["faithfulness"]
    relevancy = scores["answer_relevancy"]
    precision = scores["context_precision"]

    confidence = (
        faithfulness * WEIGHTS["faithfulness"]
        + relevancy * WEIGHTS["answer_relevancy"]
        + precision * WEIGHTS["context_precision"]
    )

    failed = [dim for dim, val in scores.items() if val < THRESHOLDS[dim]]

    logger.info(
        f"Eval -> faithfulness={faithfulness:.2f}, "
        f"relevancy={relevancy:.2f}, "
        f"precision={precision:.2f}, "
        f"confidence={confidence:.2f}, "
        f"failed={failed}"
    )

    return {
        **scores,
        "confidence": round(confidence, 4),
        "failed_dimensions": failed,
        "passed": len(failed) == 0,
    }