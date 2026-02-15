from typing import Dict, Any
from app.retrieval.state import GraphState
from app.retrieval.vector_store import vector_store


def retrieve(state: GraphState) -> Dict[str, Any]:
    """
    Retrieve documents from department-scoped vector collections.

    Uses the `departments` list from the graph state to search only
    the collections the user has access to.
    """
    print("---RETRIEVE---")
    question = state["question"]
    departments = state.get("departments", ["general"])

    # Fan-out hybrid search across allowed departments
    documents = vector_store.hybrid_search(question, departments=departments)

    print(f"   Retrieved {len(documents)} docs from departments: {departments}")
    return {"documents": documents, "question": question}
