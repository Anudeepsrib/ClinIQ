"""
Retrieve node — executes department-scoped hybrid search against the
vector store and returns matching documents.
"""

import logging
from typing import Any, Dict

from app.retrieval.state import GraphState
from app.retrieval.vector_store import vector_store

logger = logging.getLogger(__name__)


def retrieve(state: GraphState) -> Dict[str, Any]:
    """
    Retrieve documents from department-scoped vector collections.

    Uses the ``departments`` list from the graph state to search only
    the collections the user has access to.

    Args:
        state: The current graph state.

    Returns:
        Updated state with retrieved ``documents``.
    """
    logger.info("---RETRIEVE---")
    question = state["question"]
    departments = state.get("departments", ["general"])

    # Fan-out hybrid search across allowed departments
    documents = vector_store.hybrid_search(question, departments=departments)

    logger.info(
        "  Retrieved %d docs from departments: %s", len(documents), departments
    )
    return {"documents": documents, "question": question}
