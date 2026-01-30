from typing import List, TypedDict, Any
from app.schemas.models import RetrievalResult

class GraphState(TypedDict):
    """
    Represents the state of our graph.
    
    Attributes:
        question: The user's original question
        documents: List of retrieved documents
        generation: The final generated answer
    """
    question: str
    documents: List[RetrievalResult]
    generation: str
