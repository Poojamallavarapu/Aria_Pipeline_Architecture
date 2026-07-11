"""
generator.py
Grounded answer generation using hybrid retrieval (vector + BM25 + RRF)
followed by cross-encoder reranking, with a self-healing faithfulness
retry loop.
"""

import ollama

from src.retrieval.fusion import hybrid_retrieve
from src.retrieval.reranker import rerank
from src.evaluation.self_check import check_faithfulness

MODEL_NAME = "llama3.2:3b"  # llama3.1:8b was ~14min/response on cpu-basic; 1b is ~5× faster
FAITHFULNESS_THRESHOLD = 0.6
MAX_RETRIES = 2
GENERATION_OPTIONS = {"temperature": 0.0}


def build_context(results):
    context_parts = []
    for result in results:
        source = result["metadata"]["source"]
        page = result["metadata"]["page"]
        text = result["text"]
        context_parts.append(f"\nSource: {source}\nPage: {page}\n\n{text}\n")
    return "\n\n".join(context_parts)


def build_prompt_qa(query: str, context: str, retry: bool = False) -> str:
    if retry:
        warning = """
IMPORTANT:
Your previous answer included information not supported by the context.
Be extremely conservative.
ONLY state facts explicitly written in the context.
If unsure, say: "I could not find this information in the documents."
"""
    else:
        warning = ""

    return f"""
You are a cybersecurity assistant.

Use ONLY the provided context.
Do NOT use outside knowledge.

When both a definition and an example are present,
explain the definition first.

{warning}

Always mention source document and page number.

Context:
{context}

Question:
{query}

Answer:
"""


def build_prompt_triage(query: str, context: str, retry: bool = False) -> str:
    if retry:
        warning = """
IMPORTANT: Your previous response included information not supported
by the context. Be extremely conservative -- only state what is
explicitly written in the context.
"""
    else:
        warning = ""

    return f"""
You are a cybersecurity SOC triage assistant.

Use ONLY the provided context. Respond in this exact structure:

WHAT THIS IS: (matching technique/vulnerability, with ID if known)
WHY IT MATTERS: (brief severity/impact)
RECOMMENDED ACTION: (concrete next steps, only if mentioned in context)
SOURCE: (document name and page number)

{warning}

Context:
{context}

Observed activity / question:
{query}

Response:
"""


PROMPT_STRATEGIES = {
    "qa": build_prompt_qa,
    "triage": build_prompt_triage,
}


def build_prompt(query: str, context: str, retry: bool = False) -> str:
    return build_prompt_qa(query, context, retry)


def generate_answer(query: str, mode: str = "qa"):
    candidates = hybrid_retrieve(query, top_k=10, fetch_k=15)
    retrieved_chunks = rerank(query, candidates, top_k=5)
    context = build_context(retrieved_chunks)
    prompt_fn = PROMPT_STRATEGIES.get(mode, build_prompt_qa)
    prompt = prompt_fn(query=query, context=context, retry=False)

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options=GENERATION_OPTIONS,
    )
    return response["message"]["content"]


def generate_answer_self_healing(query: str, mode: str = "qa"):
    candidates = hybrid_retrieve(query, top_k=10, fetch_k=15)
    retrieved_chunks = rerank(query, candidates, top_k=5)
    context = build_context(retrieved_chunks)
    context_texts = [chunk["text"] for chunk in retrieved_chunks]
    prompt_fn = PROMPT_STRATEGIES.get(mode, build_prompt_qa)

    attempt = 0
    answer = None
    score = 0.0

    while attempt <= MAX_RETRIES:
        prompt = prompt_fn(query=query, context=context, retry=(attempt > 0))
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options=GENERATION_OPTIONS,
        )
        answer = response["message"]["content"]
        score = check_faithfulness(answer, context_texts)
        print(f"[Attempt {attempt + 1}] Faithfulness score: {score:.2f}")
        if score >= FAITHFULNESS_THRESHOLD:
            return answer, score, attempt + 1
        attempt += 1

    return answer, score, attempt


if __name__ == "__main__":
    question = input("Question: ")
    mode = input("Mode (qa/triage) [qa]: ").strip() or "qa"
    answer, score, attempts = generate_answer_self_healing(question, mode=mode)
    print(f"\n===== ANSWER (faithfulness: {score:.2f}, attempts: {attempts}) =====")
    print(answer)
