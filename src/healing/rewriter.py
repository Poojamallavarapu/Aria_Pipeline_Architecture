"""
rewriter.py
Strategy A: Query Rewriting.
"""

import logging
import ollama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REWRITE_MODEL = "llama3.2:3b"
REWRITE_OPTIONS = {"temperature": 0.0, "num_predict": 60}


def rewrite_query(original_query: str) -> str:
    prompt = f"""You are a cybersecurity search query optimizer.

Rewrite the following question into a more precise search query using
official cybersecurity terminology (e.g. NIST/OWASP/MITRE terms) that is
more likely to match technical documentation.

Original question: {original_query}

Respond with ONLY the rewritten query. No explanation, no quotes."""

    response = ollama.chat(
        model=REWRITE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options=REWRITE_OPTIONS,
    )

    rewritten = response["message"]["content"].strip()
    logger.info(f"Query rewritten: '{original_query}' -> '{rewritten}'")
    return rewritten


if __name__ == "__main__":
    query = input("Original query: ")
    rewritten = rewrite_query(query)
    print(f"\nRewritten query: {rewritten}")
