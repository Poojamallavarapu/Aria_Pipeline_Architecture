# check_loose_answers.py
import json

with open("hedging_comparison_results.json", "r", encoding="utf-8") as f:
    results = json.load(f)

flagged_questions = [
    "What is the Identify function in NIST CSF 2.0?",
    "What is the Squiblydoo attack technique?",
    "What is Registry Run Keys persistence technique?",
    "How can SQL injection be prevented?",
]

for r in results:
    if r["question"] in flagged_questions and r["variant"] == "loose":
        print(f"\n{'='*70}")
        print(f"Q: {r['question']}")
        print(f"Faithfulness: {r['faithfulness']}")
        print(f"\nANSWER:\n{r['answer']}")