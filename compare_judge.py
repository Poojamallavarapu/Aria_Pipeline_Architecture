"""
compare_judge.py
Phase 1, Step 3: independent judge comparison.

Generates answers ONCE per question (using your current best "loose"
generator prompt), then scores each answer TWICE — once with Llama 3.1
as judge, once with Mistral as judge — using the same scoring logic as
evaluator.py, but with an added forced-reasoning step before the score
(a known reliability improvement for LLM-as-judge).

Only ONE variable changes between the two passes: the judge model.
Generation, retrieval, and context are identical for both, so any
score difference is attributable to the judge, not noise elsewhere.

SCALE: 10 questions x 2 judges x 3 metrics = 60 judge calls, plus
10 generation calls = 70 Ollama calls total. Expect 1.5-4+ hours on
CPU. Run as a background job. Saves incrementally to
judge_comparison_results.json -- safe to stop and rerun, skips
anything already done.
"""

import json
import logging
import re
from pathlib import Path

import ollama

from src.retrieval.fusion import hybrid_retrieve
from src.retrieval.reranker import rerank
from src.generation.generator import build_context, build_prompt, MODEL_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESULTS_PATH = Path("judge_comparison_results.json")
GENERATION_OPTIONS = {"temperature": 0.0}
TEST_QUESTIONS_PATH = Path("data/eval/test_questions.json")

JUDGES = {
    "llama": "llama3.1:8b",
    "mistral": "mistral",
}

THRESHOLDS = {"faithfulness": 0.70, "answer_relevancy": 0.70, "context_precision": 0.60}
WEIGHTS = {"faithfulness": 0.40, "answer_relevancy": 0.35, "context_precision": 0.25}


def load_questions(path: Path = TEST_QUESTIONS_PATH) -> list[str]:
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
    return questions


QUESTIONS = load_questions()


def _extract_score(text: str) -> float:
    """Pulls the LAST number in the response, since the forced-reasoning
    prompt now produces reasoning text BEFORE the final score."""
    matches = re.findall(r"([01](?:\.\d+)?)", text)
    if matches:
        return max(0.0, min(1.0, float(matches[-1])))
    return 0.5


def _judge(prompt: str, judge_model: str) -> str:
    response = ollama.chat(
        model=judge_model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.0},
    )
    return response["message"]["content"]


def score_faithfulness(answer: str, contexts: list[str], judge_model: str) -> tuple[float, str]:
    context_text = "\n\n".join(contexts)
    prompt = f"""Rate how well the ANSWER is supported by the CONTEXT.
Every claim in the answer must be explicitly present in the context.

CONTEXT:
{context_text}

ANSWER:
{answer}

First, briefly list each distinct claim in the answer and note whether
it is supported by the context (one short line per claim).
Then, on a new final line, give ONLY a number between 0 and 1 as your
overall score. The number must be the very last thing you write."""
    raw = _judge(prompt, judge_model)
    return _extract_score(raw), raw


def score_answer_relevancy(question: str, answer: str, judge_model: str) -> tuple[float, str]:
    prompt = f"""Rate how directly and completely the ANSWER addresses the QUESTION.

QUESTION:
{question}

ANSWER:
{answer}

First, briefly note what the question is actually asking and whether
the answer addresses it fully, partially, or not at all.
Then, on a new final line, give ONLY a number between 0 and 1 as your
overall score. The number must be the very last thing you write."""
    raw = _judge(prompt, judge_model)
    return _extract_score(raw), raw


def score_context_precision(question: str, contexts: list[str], judge_model: str) -> tuple[float, str]:
    context_text = "\n\n---\n\n".join(f"Chunk {i+1}:\n{c}" for i, c in enumerate(contexts))
    prompt = f"""Count how many of the CONTEXT CHUNKS are relevant to answering the QUESTION.

QUESTION:
{question}

CONTEXT CHUNKS:
{context_text}

First, briefly state for each chunk number whether it is relevant or not.
Then, on a new final line, give ONLY a number between 0 and 1 representing
relevant_chunks / total_chunks. The number must be the very last thing you write."""
    raw = _judge(prompt, judge_model)
    return _extract_score(raw), raw


def evaluate_with_judge(question: str, answer: str, contexts: list[str], judge_model: str) -> dict:
    faithfulness, f_reason = score_faithfulness(answer, contexts, judge_model)
    relevancy, r_reason = score_answer_relevancy(question, answer, judge_model)
    precision, p_reason = score_context_precision(question, contexts, judge_model)

    confidence = (
        faithfulness * WEIGHTS["faithfulness"]
        + relevancy * WEIGHTS["answer_relevancy"]
        + precision * WEIGHTS["context_precision"]
    )
    scores = {"faithfulness": faithfulness, "answer_relevancy": relevancy, "context_precision": precision}
    failed = [dim for dim, val in scores.items() if val < THRESHOLDS[dim]]

    return {
        **scores,
        "confidence": round(confidence, 4),
        "failed_dimensions": failed,
        "passed": len(failed) == 0,
        "_reasoning": {"faithfulness": f_reason, "answer_relevancy": r_reason, "context_precision": p_reason},
    }


def generate(query: str) -> tuple[str, list[str]]:
    candidates = hybrid_retrieve(query, top_k=10, fetch_k=15)
    chunks = rerank(query, candidates, top_k=5)
    context = build_context(chunks)
    context_texts = [c["text"] for c in chunks]
    prompt = build_prompt(query, context, retry=False)
    response = ollama.chat(model=MODEL_NAME, messages=[{"role": "user", "content": prompt}], options=GENERATION_OPTIONS)
    return response["message"]["content"], context_texts


def load_results() -> dict:
    if RESULTS_PATH.exists():
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_results(results: dict) -> None:
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


def run():
    results = load_results()
    logger.info(f"Resuming with {len(results)} questions already in results.")

    for question in QUESTIONS:
        if question not in results:
            results[question] = {}

        # Generate ONCE per question (shared across both judges)
        if "answer" not in results[question]:
            logger.info(f"Generating answer for: {question}")
            answer, contexts = generate(question)
            results[question]["answer"] = answer
            results[question]["contexts"] = contexts
            save_results(results)
        else:
            answer = results[question]["answer"]
            contexts = results[question]["contexts"]

        for judge_name, judge_model in JUDGES.items():
            if judge_name in results[question]:
                logger.info(f"SKIP (already judged by {judge_name}): {question}")
                continue

            logger.info(f"Judging [{judge_name}]: {question}")
            eval_result = evaluate_with_judge(question, answer, contexts, judge_model)
            results[question][judge_name] = eval_result
            save_results(results)
            logger.info(
                f"DONE [{judge_name}] faithfulness={eval_result['faithfulness']:.2f} "
                f"relevancy={eval_result['answer_relevancy']:.2f} "
                f"precision={eval_result['context_precision']:.2f}"
            )

    print_summary(results)


def print_summary(results: dict) -> None:
    print("\n" + "=" * 80)
    print("SUMMARY: Llama judge vs Mistral judge (same answers, same context)")
    print("=" * 80)

    llama_scores = {"faithfulness": [], "answer_relevancy": [], "context_precision": []}
    mistral_scores = {"faithfulness": [], "answer_relevancy": [], "context_precision": []}

    for question, data in results.items():
        print(f"\nQ: {question}")
        if "llama" in data:
            l = data["llama"]
            print(f"  [llama  ] faithfulness={l['faithfulness']:.2f}  relevancy={l['answer_relevancy']:.2f}  "
                  f"precision={l['context_precision']:.2f}  confidence={l['confidence']:.2f}")
            for k in llama_scores:
                llama_scores[k].append(l[k])
        if "mistral" in data:
            m = data["mistral"]
            print(f"  [mistral] faithfulness={m['faithfulness']:.2f}  relevancy={m['answer_relevancy']:.2f}  "
                  f"precision={m['context_precision']:.2f}  confidence={m['confidence']:.2f}")
            for k in mistral_scores:
                mistral_scores[k].append(m[k])
        if "llama" in data and "mistral" in data:
            delta = data["llama"]["faithfulness"] - data["mistral"]["faithfulness"]
            flag = " <-- judges disagree significantly" if abs(delta) > 0.2 else ""
            print(f"  faithfulness delta (llama - mistral): {delta:+.2f}{flag}")

    print("\n" + "-" * 80)
    print("AVERAGES")
    for k in llama_scores:
        if llama_scores[k] and mistral_scores[k]:
            l_avg = sum(llama_scores[k]) / len(llama_scores[k])
            m_avg = sum(mistral_scores[k]) / len(mistral_scores[k])
            print(f"  {k:20s} llama={l_avg:.3f}  mistral={m_avg:.3f}  delta={l_avg - m_avg:+.3f}")

    print("\nFull results (incl. judge reasoning) saved to:", RESULTS_PATH.resolve())


if __name__ == "__main__":
    run()