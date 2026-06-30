"""
pipeline.py
Single entry point for the API/UI layer. Wraps the healing engine.
"""

import time
from src.healing.engine import ask_aria_healing


def ask_aria(question: str, mode: str = "qa") -> dict:
    """
    Run the full ARIA pipeline for a single question/observation.

    Returns:
    {
        "answer": str,
        "confidence": float,
        "scores": {faithfulness, answer_relevancy, context_precision},
        "healing_triggered": bool,
        "healing_attempts": int,
        "strategies_used": [str, ...],
        "passed": bool,
        "latency_ms": int,
        "mode": str
    }
    """
    start = time.time()
    result = ask_aria_healing(question, mode=mode)
    result["latency_ms"] = int((time.time() - start) * 1000)
    result["mode"] = mode
    return result


if __name__ == "__main__":
    question = input("Question/Observation: ")
    mode = input("Mode (qa/triage) [qa]: ").strip() or "qa"
    result = ask_aria(question, mode=mode)

    print(f"\n===== ANSWER (mode: {result['mode']}, latency: {result['latency_ms']}ms) =====")
    print(result["answer"])
    print(f"\nConfidence: {result['confidence']:.2f}")
    print(f"Passed: {result['passed']}")