"""
run_eval.py
Runs ARIA on the test set and evaluates with Ragas using local Ollama models.
"""

import json
import logging
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.run_config import RunConfig

from langchain_ollama import ChatOllama, OllamaEmbeddings

from src.retrieval.fusion import hybrid_retrieve
from src.retrieval.reranker import rerank
from src.generation.generator import generate_answer_self_healing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_SET_PATH = "data/eval/test_questions_50.json"


def run_pipeline_for_eval(question: str):
    candidates = hybrid_retrieve(question, top_k=10, fetch_k=15)
    reranked = rerank(question, candidates, top_k=5)

    contexts = [r["text"] for r in reranked]

    answer, score, attempts = generate_answer_self_healing(question)

    logger.info(f"  -> faithfulness (self-check): {score:.2f}, attempts: {attempts}")

    return answer, contexts


def build_eval_dataset(test_set_path: str) -> Dataset:
    with open(test_set_path, "r") as f:
        test_cases = json.load(f)

    questions, answers, contexts_list, ground_truths = [], [], [], []

    for i, case in enumerate(test_cases):
        question = case["question"]
        ground_truth = case["ground_truth"]

        logger.info(f"[{i+1}/{len(test_cases)}] Running: {question}")

        answer, contexts = run_pipeline_for_eval(question)

        questions.append(question)
        answers.append(answer)
        contexts_list.append(contexts)
        ground_truths.append(ground_truth)

    return Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts_list,
        "ground_truth": ground_truths,
    })


if __name__ == "__main__":
    dataset = build_eval_dataset(TEST_SET_PATH)

    logger.info("Setting up local Ollama judge for Ragas...")

    judge_llm = LangchainLLMWrapper(ChatOllama(model="llama3.1:8b", temperature=0))
    judge_embeddings = LangchainEmbeddingsWrapper(OllamaEmbeddings(model="nomic-embed-text"))

    logger.info("Running Ragas evaluation...")

    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision],
        llm=judge_llm,
        embeddings=judge_embeddings,
        run_config=RunConfig(timeout=600, max_workers=1),
    )

    print("\n===== RAGAS EVALUATION RESULTS =====")
    print(result)

    df = result.to_pandas()
    df.to_csv("data/eval/eval_results.csv", index=False)
    print("\nDetailed results saved to data/eval/eval_results.csv")