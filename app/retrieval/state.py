from typing import List, TypedDict, Any, Optional
from app.schemas.models import RetrievalResult


class GraphState(TypedDict):
    """
    Represents the state of the retrieval graph.

    Attributes:
        question:    The user's original question
        documents:   List of retrieved documents
        generation:  The final generated answer
        role:        User role (for role-aware generation)
        departments: Departments the user can access
        user_id:     Username for audit trail
    """
    question: str
    documents: List[RetrievalResult]
    generation: str
    role: str
    departments: List[str]
    user_id: str
