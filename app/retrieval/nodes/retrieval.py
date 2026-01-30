from typing import Dict, Any
from app.retrieval.state import GraphState
from app.retrieval.vector_store import vector_store

def retrieve(state: GraphState) -> Dict[str, Any]:
    """
    Retrieve documents from vectorstore
    
    Args:
        state (dict): The current graph state
        
    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    question = state["question"]
    documents = vector_store.search(question)
    return {"documents": documents, "question": question}
