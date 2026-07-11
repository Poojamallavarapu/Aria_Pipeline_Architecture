"""
self_check.py
Lightweight runtime faithfulness check for self-healing.
"""

import re
import ollama

JUDGE_MODEL = "llama3.2:3b"


def extract_score(text: str) -> float:
    match = re.search(r"([01](?:\.\d+)?)", text)
    if match:
        return max(0.0, min(1.0, float(match.group(1))))
    return 0.5


def check_faithfulness(answer: str, contexts: list[str]) -> float:
    context_text = "\n\n".join(contexts)
    prompt = f"""Rate how well the ANSWER is supported by the CONTEXT.

CONTEXT:
{context_text}

ANSWER:
{answer}

Respond with ONLY a number between 0 and 1 (e.g. 0.8). No other text."""

    response = ollama.chat(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.0},
    )
    return extract_score(response["message"]["content"])
