from langgraph.graph import END, StateGraph
from app.retrieval.state import GraphState
from app.retrieval.nodes.retrieval import retrieve
from app.retrieval.nodes.grading import grade_documents
from app.retrieval.nodes.generation import generate

def decide_to_generate(state: GraphState):
    """
    Determines whether to generate an answer, or end.
    """
    if not state["documents"]:
        # No relevant documents found
        return "end"
    else:
        # We have relevant documents, so generate answer
        return "generate"

workflow = StateGraph(GraphState)

# Add nodes
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)

# Build graph
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "generate": "generate",
        "end": END
    }
)
workflow.add_edge("generate", END)

# Compile
app_graph = workflow.compile()
