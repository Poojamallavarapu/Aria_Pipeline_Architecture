"""
compare_hedging.py
Step 1 of the diagnostic plan: isolate whether RAGAS-style faithfulness
scoring penalizes honest "I could not find this" hedging language,
independent of whether the underlying answer is actually well-grounded.

Run from your ARIA project root (same level as src/), with venv active
and Ollama running locally.

WHAT THIS DOES:
  Loads all questions from data/eval/test_questions.json automatically.
  For each question, generates TWO answers:
    - "strict"  : your current build_prompt() with the hedging instruction
    - "loose"   : same prompt, hedging instruction removed
  Then scores both with your real evaluator.evaluate_answer().
  Saves everything to hedging_comparison_results.json incrementally,
  so a crash/interrupt on CPU doesn't lose completed work -- safe to
  stop and rerun the same command, it skips anything already done.

SCALE NOTE: with 10 questions this is 10 x 2 variants x (1 generate +
3 judge calls) = 80 Ollama calls total. Expect roughly 1.5-4 hours on
CPU-only hardware based on your prior batch eval timings. Run this as
a background job, not interactively -- kick it off and check back.

If load_questions() can't find the question text in your JSON file,
see the KEY_CANDIDATES list inside that function and add your actual
key name.
"""

import json
import logging
from pathlib import Path

import ollama

from src.retrieval.fusion import hybrid_retrieve
from src.retrieval.reranker import rerank
from src.generation.generator import build_context, MODEL_NAME
from src.evaluation.evaluator import evaluate_answer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESULTS_PATH = Path("hedging_comparison_results.json")
GENERATION_OPTIONS = {"temperature": 0.0}
TEST_QUESTIONS_PATH = Path("data/eval/test_questions.json")


def load_questions(path: Path = TEST_QUESTIONS_PATH) -> list[str]:
    """Loads questions from your real test_questions.json.

    Handles a few common shapes automatically:
      - ["question 1", "question 2", ...]
      - [{"question": "...", "ground_truth": "..."}, ...]
      - [{"q": "...", ...}, ...]
      - {"questions": [...]}  (wrapped in a dict)

    If your file uses a different key for the question text, edit the
    KEY_CANDIDATES list below to match.
    """
    KEY_CANDIDATES = ["question", "q", "query", "input"]

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "questions" in data:
        data = data["questions"]

    questions = []
    for item in data:
        if isinstance(item, str):
            questions.append(item)
        elif isinstance(item, dict):
            for key in KEY_CANDIDATES:
                if key in item:
                    questions.append(item[key])
                    break
            else:
                raise ValueError(
                    f"Could not find a question field in: {item}. "
                    f"Add the correct key to KEY_CANDIDATES in load_questions()."
                )
    return questions


QUESTIONS = load_questions()


def build_prompt_strict(query: str, context: str) -> str:
    """Your current production prompt -- includes the hedging instruction."""
    return f"""
You are a cybersecurity assistant.

Use ONLY the provided context.
Do NOT use outside knowledge.
Do NOT add explanations that are not explicitly present.

When both a definition and an example are present,
explain the definition first.

If the information is unavailable, say:
"I could not find this information in the documents."

Always mention source document and page number.

Context:
{context}

Question:
{query}

Answer:
"""


def build_prompt_loose(query: str, context: str) -> str:
    """Same prompt, hedging instruction removed. Still grounded -- only
    the explicit 'say if you don't know' line is dropped, so this isn't
    testing 'allow hallucination', just 'allow a more natural answer
    when context is thin'."""
    return f"""
You are a cybersecurity assistant.

Use ONLY the provided context.
Do NOT use outside knowledge.

When both a definition and an example are present,
explain the definition first.

Always mention source document and page number.

Context:
{context}

Question:
{query}

Answer:
"""


def generate(query: str, prompt_fn) -> tuple[str, list[str]]:
    candidates = hybrid_retrieve(query, top_k=10, fetch_k=15)
    chunks = rerank(query, candidates, top_k=5)
    context = build_context(chunks)
    context_texts = [c["text"] for c in chunks]
    prompt = prompt_fn(query, context)
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options=GENERATION_OPTIONS,
    )
    return response["message"]["content"], context_texts


def load_results() -> list[dict]:
    if RESULTS_PATH.exists():
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_results(results: list[dict]) -> None:
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


def already_done(results: list[dict], question: str, variant: str) -> bool:
    return any(r["question"] == question and r["variant"] == variant for r in results)


def run():
    results = load_results()
    logger.info(f"Resuming with {len(results)} results already saved.")

    for question in QUESTIONS:
        for variant, prompt_fn in [("strict", build_prompt_strict), ("loose", build_prompt_loose)]:
            if already_done(results, question, variant):
                logger.info(f"SKIP (already done): [{variant}] {question}")
                continue

            logger.info(f"Generating [{variant}] for: {question}")
            answer, contexts = generate(question, prompt_fn)

            logger.info("Evaluating...")
            eval_result = evaluate_answer(question, answer, contexts)

            record = {
                "question": question,
                "variant": variant,
                "answer": answer,
                "faithfulness": eval_result["faithfulness"],
                "answer_relevancy": eval_result["answer_relevancy"],
                "context_precision": eval_result["context_precision"],
                "confidence": eval_result["confidence"],
                "passed": eval_result["passed"],
                "failed_dimensions": eval_result["failed_dimensions"],
            }
            results.append(record)
            save_results(results)  # save after every single call -- CPU is slow, don't lose progress
            logger.info(
                f"DONE [{variant}] faithfulness={record['faithfulness']:.2f} "
                f"relevancy={record['answer_relevancy']:.2f} "
                f"precision={record['context_precision']:.2f}"
            )

    print_summary(results)


def print_summary(results: list[dict]) -> None:
    print("\n" + "=" * 70)
    print("SUMMARY: strict (hedging) vs loose (no hedging instruction)")
    print("=" * 70)
    by_question: dict[str, dict[str, dict]] = {}
    for r in results:
        by_question.setdefault(r["question"], {})[r["variant"]] = r

    for question, variants in by_question.items():
        print(f"\nQ: {question}")
        for variant in ["strict", "loose"]:
            if variant in variants:
                r = variants[variant]
                print(
                    f"  [{variant:6s}] faithfulness={r['faithfulness']:.2f}  "
                    f"relevancy={r['answer_relevancy']:.2f}  "
                    f"precision={r['context_precision']:.2f}  "
                    f"confidence={r['confidence']:.2f}  passed={r['passed']}"
                )
        if "strict" in variants and "loose" in variants:
            delta = variants["strict"]["faithfulness"] - variants["loose"]["faithfulness"]
            flag = " <-- hedging penalty suspected" if delta < -0.05 else ""
            print(f"  strict-vs-loose faithfulness delta: {delta:+.2f}{flag}")

    print("\nFull results saved to:", RESULTS_PATH.resolve())


if __name__ == "__main__":
    run()