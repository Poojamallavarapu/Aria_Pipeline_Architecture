"""
router.py
Agentic strategy router with anti-repeat guard.
"""

import logging
import ollama

from src.healing.memory import summarize_strategy_success_rates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROUTER_MODEL = "llama3.2:3b"
ROUTER_OPTIONS = {"temperature": 0.0, "num_predict": 50}

ALL_STRATEGIES = ["A-query_rewrite", "B-expand_mmr", "C-decomposition"]

STRATEGY_DESCRIPTIONS = {
    "A-query_rewrite": (
        "A-query_rewrite: Rewrites the search query with more precise technical "
        "terminology. Best when retrieved documents don't match the question's "
        "topic at all (low context_precision, nothing relevant found)."
    ),
    "B-expand_mmr": (
        "B-expand_mmr: Retrieves more chunks (10 instead of 5) and diversifies "
        "them. Best when the topic is right but there isn't enough evidence to "
        "fully ground an answer (low faithfulness, but relevant docs DO exist)."
    ),
    "C-decomposition": (
        "C-decomposition: Breaks the question into 2-3 simpler sub-questions, "
        "answers each, then combines them. Best when the question is complex "
        "or covers multiple concepts (low answer_relevancy)."
    ),
}


def choose_strategy(
    question: str,
    failed_dimensions: list[str],
    scores: dict,
    tried_strategies: list[str] | None = None,
) -> str:
    tried_strategies = tried_strategies or []
    primary_failure = failed_dimensions[0] if failed_dimensions else "unknown"
    memory_summary = summarize_strategy_success_rates(primary_failure)

    available = [s for s in ALL_STRATEGIES if s not in tried_strategies] or ALL_STRATEGIES
    forced_fallback = len(available) < len(ALL_STRATEGIES)

    descriptions = "\n".join(f"- {STRATEGY_DESCRIPTIONS[s]}" for s in available)

    already_tried_note = (
        f"\nALREADY TRIED THIS SESSION (did not resolve the issue, do NOT repeat): "
        f"{', '.join(tried_strategies)}" if tried_strategies else ""
    )

    prompt = f"""You are choosing a repair strategy for a RAG system's failed answer.

QUESTION: {question}

FAILED DIMENSIONS: {', '.join(failed_dimensions)}
SCORES: faithfulness={scores['faithfulness']:.2f}, relevancy={scores['answer_relevancy']:.2f}, precision={scores['context_precision']:.2f}
{already_tried_note}

Available strategies:
{descriptions}

PAST PERFORMANCE for this failure type: {memory_summary}

Choose exactly ONE strategy from the available list above to try next.
Respond with ONLY the strategy code. No explanation."""

    response = ollama.chat(
        model=ROUTER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options=ROUTER_OPTIONS,
    )

    choice = response["message"]["content"].strip()

    for valid in available:
        if valid in choice:
            logger.info(
                f"Agentic router chose: {valid} (failed: {primary_failure}, "
                f"memory: {memory_summary}, excluded: {tried_strategies if forced_fallback else 'none'})"
            )
            return valid

    fallback = available[0]
    logger.warning(f"Router gave unparseable choice '{choice}', falling back to {fallback}")
    return fallback
