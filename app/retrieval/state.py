"""
LangGraph state definition for the ClinIQ healthcare RAG pipeline.

This TypedDict defines the complete state that flows through the graph,
including fields for observability, retry management, and audit trails.
"""

from typing import Any, Dict, List, TypedDict

from app.schemas.models import RetrievalResult


class GraphState(TypedDict):
    """
    Represents the state of the ClinIQ retrieval graph.

    Attributes:
        question:              The user's current question (may be rewritten)
        documents:             List of retrieved documents
        generation:            The final generated answer
        role:                  User role (for role-aware generation)
        departments:           Departments the user can access
        user_id:               Username for audit trail
        retry_count:           Number of query transform retries (capped)
        hallucination_score:   'yes' (grounded) or 'no' (hallucinated)
        query_transformations: Audit trail of all query rewrites
        metadata:              LangSmith tags (department, user_role, etc.)
    """

    question: str
    documents: List[RetrievalResult]
    generation: str
    role: str
    departments: List[str]
    user_id: str
    retry_count: int
    hallucination_score: str
    query_transformations: List[str]
    metadata: Dict[str, Any]
    clarification_needed: bool
    clarification_options: List[str]
