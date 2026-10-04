"""
engine.py
Adaptive Self-Healing Orchestrator.

Uses:
- router.py    -> choose_strategy()  (agentic strategy selection)
- memory.py    -> save_memory_entry() (logs outcomes for future routing)
- observability/tracer.py -> langfuse (full pipeline tracing)

Supports multiple output modes (mode="qa" or mode="triage") via
generator.py's PROMPT_STRATEGIES registry, so the same retrieval +
healing + memory + agentic router pipeline can serve different output
shapes without duplicating pipeline logic.
"""

import logging
import ollama
import time

from src.retrieval.fusion import hybrid_retrieve
from src.retrieval.reranker import rerank
from src.generation.generator import build_context, PROMPT_STRATEGIES, MODEL_NAME
from src.evaluation.evaluator import evaluate_answer

from src.healing.rewriter import rewrite_query
from src.healing.expander import expand_retrieval
from src.healing.decomposer import decompose_and_answer

from src.healing.router import choose_strategy
from src.healing.memory import save_memory_entry
from src.observability.tracer import langfuse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GENERATION_OPTIONS = {"temperature": 0.0, "num_predict": 350}
MAX_HEALING_ATTEMPTS = 3


def _generate(query: str, chunks: list[dict], mode: str = "qa") -> str:
    context = build_context(chunks)
    prompt_fn = PROMPT_STRATEGIES.get(mode, PROMPT_STRATEGIES["qa"])
    prompt = prompt_fn(query, context, retry=False)

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options=GENERATION_OPTIONS,
    )

    return response["message"]["content"]


def ask_aria_healing(question: str, mode: str = "qa") -> dict:
    """
    Adaptive self-healing pipeline. Reusable across modes.

    mode: "qa" for plain question-answering, "triage" for SOC-style
    structured incident response. Same retrieval/healing/memory engine,
    only the generation prompt template changes.

    Every call creates a Langfuse trace with nested spans for each
    pipeline stage (retrieval, reranking, generation, evaluation, and
    each healing attempt).

    Returns:
    {
        answer,
        confidence,
        scores,
        healing_triggered,
        healing_attempts,
        strategies_used,
        passed
    }
    """

    trace = langfuse.trace(name="aria_query", input={"question": question, "mode": mode})
    t0 = time.time()

    query = question

    retrieval_span = trace.span(name="hybrid_retrieval", input={"query": query})
    candidates = hybrid_retrieve(query, top_k=10, fetch_k=15)
    retrieval_span.end(output={"num_candidates": len(candidates)})

    rerank_span = trace.span(name="reranking", input={"num_candidates": len(candidates)})
    chunks = rerank(query, candidates, top_k=5)
    contexts = [c["text"] for c in chunks]
    rerank_span.end(output={"num_chunks": len(chunks)})

    gen_span = trace.span(name="generation", input={"mode": mode})
    answer = _generate(query, chunks, mode=mode)
    gen_span.end(output={"answer": answer})

    eval_span = trace.span(name="evaluation")
    result = evaluate_answer(question, answer, contexts)
    eval_span.end(output=result)

    strategies_used = []
    attempt = 0

    best_answer = answer
    best_confidence = result["confidence"]
    best_result = result

    while not result["passed"] and attempt < MAX_HEALING_ATTEMPTS:

        heal_span = trace.span(name=f"healing_attempt_{attempt + 1}")
        confidence_before_attempt = result["confidence"]

        strategy_choice = choose_strategy(
            question,
            result["failed_dimensions"],
            result,
            tried_strategies=strategies_used,
        )

        heal_span.update(input={
            "failed_dimensions": result["failed_dimensions"],
            "strategy_chosen": strategy_choice,
        })

        logger.info(
            f"[Healing attempt {attempt + 1}] Strategy: {strategy_choice}"
        )

        # -----------------------------
        # Strategy A : Query Rewrite
        # -----------------------------
        if strategy_choice == "A-query_rewrite":

            query = rewrite_query(question)

            candidates = hybrid_retrieve(
                query,
                top_k=10,
                fetch_k=15
            )

            chunks = rerank(query, candidates, top_k=5)
            contexts = [c["text"] for c in chunks]

            answer = _generate(query, chunks, mode=mode)

            strategies_used.append("A-query_rewrite")

        # -----------------------------
        # Strategy B : Expansion + MMR
        # -----------------------------
        elif strategy_choice == "B-expand_mmr":

            chunks = expand_retrieval(
                question,
                expanded_top_k=10
            )

            contexts = [c["text"] for c in chunks]

            answer = _generate(question, chunks, mode=mode)

            strategies_used.append("B-expand_mmr")

        # -----------------------------
        # Strategy C : Decomposition
        # -----------------------------
        elif strategy_choice == "C-decomposition":

            # Note: sub-question answering inside decompose_and_answer
            # always uses QA-style generation internally, even when the
            # outer mode is "triage" -- the final synthesis step is what
            # carries the overall answer forward for evaluation. This is
            # a known, intentional simplification (see project notes).
            answer = decompose_and_answer(question)

            strategies_used.append("C-decomposition")

        else:
            logger.warning("Unknown strategy returned.")
            heal_span.end(output={"error": "unknown_strategy"})
            break

        result_new = evaluate_answer(
            question,
            answer,
            contexts
        )

        heal_span.end(output={
            "confidence_after": result_new["confidence"],
            "improved": result_new["confidence"] > confidence_before_attempt,
        })

        save_memory_entry(
            question=question,
            failed_dimension=(
                result["failed_dimensions"][0]
                if result["failed_dimensions"]
                else "unknown"
            ),
            strategy_used=strategy_choice,
            confidence_before=confidence_before_attempt,
            confidence_after=result_new["confidence"],
        )

        result = result_new
        attempt += 1

        if result["confidence"] > best_confidence:
            best_answer = answer
            best_confidence = result["confidence"]
            best_result = result

    total_latency_ms = int((time.time() - t0) * 1000)

    trace.update(
        output={
            "answer": best_answer,
            "confidence": best_result["confidence"],
            "passed": best_result["passed"],
        },
        metadata={
            "latency_ms": total_latency_ms,
            "healing_attempts": attempt,
            "strategies_used": strategies_used,
        },
    )
    langfuse.flush()
    print("Langfuse trace flushed.")

    return {
        "answer": best_answer,
        "confidence": best_result["confidence"],
        "scores": {
            "faithfulness": best_result["faithfulness"],
            "answer_relevancy": best_result["answer_relevancy"],
            "context_precision": best_result["context_precision"],
        },
        "healing_triggered": attempt > 0,
        "healing_attempts": attempt,
        "strategies_used": strategies_used,
        "passed": best_result["passed"],
    }


if __name__ == "__main__":

    question = input("Question/Observation: ")
    mode = input("Mode (qa/triage) [qa]: ").strip() or "qa"

    result = ask_aria_healing(question, mode=mode)

    print("\n===== FINAL ANSWER =====")
    print(result["answer"])

    print(f"\nConfidence: {result['confidence']:.2f}")
    print(f"Scores: {result['scores']}")
    print(f"Healing triggered: {result['healing_triggered']}")
    print(f"Attempts: {result['healing_attempts']}")
    print(f"Strategies used: {result['strategies_used']}")
    print(f"Passed: {result['passed']}")