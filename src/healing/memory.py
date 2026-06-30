"""
memory.py
Lightweight memory of past healing attempts, used to inform the agentic
router's strategy choice (Step 3, "memory" upgrade).
"""

import json
from pathlib import Path

MEMORY_PATH = Path("healing_memory.json")


def load_memory() -> list[dict]:
    if MEMORY_PATH.exists():
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_memory_entry(question: str, failed_dimension: str, strategy_used: str,
                       confidence_before: float, confidence_after: float) -> None:
    memory = load_memory()
    memory.append({
        "question": question,
        "failed_dimension": failed_dimension,
        "strategy_used": strategy_used,
        "confidence_before": confidence_before,
        "confidence_after": confidence_after,
        "improved": confidence_after > confidence_before,
    })
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)


def get_relevant_memory(failed_dimension: str, limit: int = 5) -> list[dict]:
    """Return past attempts that failed on the same dimension, most recent first."""
    memory = load_memory()
    relevant = [m for m in memory if m["failed_dimension"] == failed_dimension]
    return relevant[-limit:]


def summarize_strategy_success_rates(failed_dimension: str) -> str:
    """Produces a short text summary the LLM router can read, e.g.
    'For faithfulness failures: Strategy B worked 3/4 times, Strategy A worked 0/1 times.'
    """
    relevant = get_relevant_memory(failed_dimension, limit=20)
    if not relevant:
        return "No past examples for this failure type yet."

    by_strategy: dict[str, list[bool]] = {}
    for m in relevant:
        by_strategy.setdefault(m["strategy_used"], []).append(m["improved"])

    lines = []
    for strategy, outcomes in by_strategy.items():
        success = sum(outcomes)
        total = len(outcomes)
        lines.append(f"{strategy} worked {success}/{total} times")

    return "; ".join(lines)