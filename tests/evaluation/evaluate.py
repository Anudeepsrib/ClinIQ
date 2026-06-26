import json
from pathlib import Path

import pandas as pd

from app.core.config import settings
from app.retrieval.graph import app_graph

EVAL_DIR = Path(__file__).resolve().parent
POLICY_DATASET_PATH = EVAL_DIR / "retrieval_eval_dataset.jsonl"
LEGACY_CSV_PATH = EVAL_DIR / "test_set.csv"

try:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import answer_relevance, context_precision, faithfulness
except ImportError as exc:
    raise SystemExit(
        "Optional RAGAS evaluation dependencies are not installed. "
        "Install a patched RAGAS release before running this script."
    ) from exc

def _load_eval_rows() -> list[dict]:
    if POLICY_DATASET_PATH.exists():
        return [
            json.loads(line)
            for line in POLICY_DATASET_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    if LEGACY_CSV_PATH.exists():
        df = pd.read_csv(LEGACY_CSV_PATH)
        return [
            {
                "id": f"legacy_{idx}",
                "question": row["question"],
                "ground_truth": row["ground_truth"],
                "role": "viewer",
                "departments": ["general"],
                "expected_doc_ids": [],
            }
            for idx, row in df.iterrows()
        ]

    print("Test set not found. Add retrieval_eval_dataset.jsonl or run generate_test_set.py.")
    return []


def _source_to_doc_id(source: str) -> str:
    stem = Path(source).stem
    parts = stem.split("-")
    if len(parts) >= 3:
        return "-".join(parts[:3])
    return stem


def _retrieved_doc_ids(docs) -> set[str]:
    ids = set()
    for doc in docs:
        metadata = getattr(doc, "metadata", {}) or {}
        if metadata.get("doc_id"):
            ids.add(metadata["doc_id"])
        source = getattr(doc, "source", "")
        if source:
            ids.add(_source_to_doc_id(source))
    return ids


def evaluate_rag():
    rows = _load_eval_rows()
    if not rows:
        return

    questions = [row["question"] for row in rows]
    ground_truths = [row["ground_truth"] for row in rows]

    answers = []
    contexts = []
    retrieval_rows = []

    print(f"Running evaluation on {len(questions)} questions...")

    for row in rows:
        # Invoke RAG pipeline
        result = app_graph.invoke({
            "question": row["question"],
            "role": row.get("role", "viewer"),
            "departments": row.get("departments", ["general"]),
            "user_id": "evaluation",
            "llm_provider": settings.LLM_PROVIDER,
            "retry_count": 0,
            "hallucination_score": "",
            "query_transformations": [],
            "metadata": {},
            "clarification_needed": False,
            "clarification_options": [],
        })

        # Extract answer and retrieved contexts
        answer = result["generation"]
        retrieved_docs = [doc.content for doc in result["documents"]]

        answers.append(answer)
        contexts.append(retrieved_docs)

        expected_doc_ids = set(row.get("expected_doc_ids", []))
        retrieved_doc_ids = _retrieved_doc_ids(result["documents"])
        retrieval_rows.append(
            {
                "id": row["id"],
                "expected_doc_ids": ",".join(sorted(expected_doc_ids)),
                "retrieved_doc_ids": ",".join(sorted(retrieved_doc_ids)),
                "hit": bool(expected_doc_ids & retrieved_doc_ids) if expected_doc_ids else None,
            }
        )

    # Prepare dataset for RAGAS
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }
    dataset = Dataset.from_dict(data)

    # Run evaluation
    result = evaluate(
        dataset=dataset,
        metrics=[
            context_precision,
            faithfulness,
            answer_relevance,
        ],
    )

    print("Evaluation Results:")
    print(result)
    result.to_pandas().to_csv(EVAL_DIR / "results.csv", index=False)

    retrieval_df = pd.DataFrame(retrieval_rows)
    retrieval_df.to_csv(EVAL_DIR / "retrieval_hits.csv", index=False)
    if retrieval_df["hit"].notna().any():
        hit_rate = retrieval_df["hit"].dropna().mean()
        print(f"Retrieval hit rate: {hit_rate:.2%}")

if __name__ == "__main__":
    evaluate_rag()
