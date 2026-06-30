"""
measure_healing_rate.py
Benchmarks the self-healing engine: what % of healing attempts actually
improve confidence? Runs a batch of questions likely to need healing,
logs results incrementally (safe to stop/resume), and reports the rate.
"""

import json
import logging
from pathlib import Path

from src.healing.engine import ask_aria_healing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QUESTIONS_PATH = Path("data/eval/healing_test_questions.json")
RESULTS_PATH = Path("healing_rate_results.json")


def load_questions() -> list[str]:
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_results() -> dict:
    if RESULTS_PATH.exists():
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_results(results: dict) -> None:
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


def run():
    questions = load_questions()
    results = load_results()

    for question in questions:
        if question in results:
            logger.info(f"SKIP (already done): {question}")
            continue

        logger.info(f"Running: {question}")
        result = ask_aria_healing(question, mode="qa")

        results[question] = {
            "confidence": result["confidence"],
            "passed": result["passed"],
            "healing_triggered": result["healing_triggered"],
            "healing_attempts": result["healing_attempts"],
            "strategies_used": result["strategies_used"],
        }
        save_results(results)
        logger.info(
            f"DONE: confidence={result['confidence']:.2f}, "
            f"passed={result['passed']}, "
            f"healing_triggered={result['healing_triggered']}, "
            f"attempts={result['healing_attempts']}"
        )

    print_summary(results)


def print_summary(results: dict) -> None:
    total = len(results)
    needed_healing = [r for r in results.values() if r["healing_triggered"]]
    healing_passed = [r for r in needed_healing if r["passed"]]
    no_healing_needed = [r for r in results.values() if not r["healing_triggered"]]

    print("\n" + "=" * 70)
    print("HEALING SUCCESS RATE BENCHMARK")
    print("=" * 70)
    print(f"Total questions tested: {total}")
    print(f"Passed without healing: {len(no_healing_needed)} ({len(no_healing_needed)/total*100:.0f}%)")
    print(f"Required healing: {len(needed_healing)} ({len(needed_healing)/total*100:.0f}%)")
    if needed_healing:
        rate = len(healing_passed) / len(needed_healing) * 100
        print(f"Healing success rate (recovered to passing): {len(healing_passed)}/{len(needed_healing)} ({rate:.0f}%)")

    avg_attempts = sum(r["healing_attempts"] for r in needed_healing) / len(needed_healing) if needed_healing else 0
    print(f"Average attempts when healing triggered: {avg_attempts:.1f}")

    print("\nPer-question detail:")
    for q, r in results.items():
        status = "✅ passed" if r["passed"] else "❌ failed"
        healed = f" (healed via {','.join(r['strategies_used'])})" if r["healing_triggered"] else " (no healing needed)"
        print(f"  [{status}] {q}{healed}")

    print(f"\nFull results saved to: {RESULTS_PATH.resolve()}")


if __name__ == "__main__":
    run()