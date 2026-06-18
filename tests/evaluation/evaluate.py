import pandas as pd

from app.core.config import settings
from app.retrieval.graph import app_graph

try:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import answer_relevance, context_precision, faithfulness
except ImportError as exc:
    raise SystemExit(
        "Optional RAGAS evaluation dependencies are not installed. "
        "Install a patched RAGAS release before running this script."
    ) from exc

def evaluate_rag():
    # Load test set
    try:
        df = pd.read_csv("tests/evaluation/test_set.csv")
    except FileNotFoundError:
        print("Test set not found. Run generate_test_set.py first.")
        return

    questions = df["question"].tolist()
    ground_truths = df["ground_truth"].tolist()
    
    answers = []
    contexts = []

    print(f"Running evaluation on {len(questions)} questions...")

    for query in questions:
        # Invoke RAG pipeline
        result = app_graph.invoke({
            "question": query,
            "role": "viewer",
            "departments": ["general"],
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
    result.to_pandas().to_csv("tests/evaluation/results.csv", index=False)

if __name__ == "__main__":
    evaluate_rag()
