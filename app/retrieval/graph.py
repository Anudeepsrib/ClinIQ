"""
ClinIQ — Stateful LangGraph RAG pipeline.

This module defines the complete graph with 6 nodes:

    clarification_check → retrieve → grade_documents → generate → hallucination_check
          |                               ↑                              |
          | (if ambiguous)                |__ transform_query ←←←←←←←←←|
          ↓                                      (if no docs)       (if hallucinated)
         END

If the user's query is ambiguous, clarification_check short-circuits the
pipeline and returns clarifying options — no retrieval or LLM generation is
performed. This mimics Claude's behaviour of asking specific questions rather
than guessing.

Conditional routing ensures the pipeline retries with query transformation
when documents are irrelevant, and regenerates when the answer is not grounded
in the clinical context. Retries are capped at ``MAX_QUERY_RETRIES`` (default 3).
"""

import logging

from langgraph.graph import END, StateGraph

from app.core.config import settings
from app.retrieval.nodes.clarification import clarification_check
from app.retrieval.nodes.generation import generate
from app.retrieval.nodes.grading import grade_documents
from app.retrieval.nodes.hallucination import hallucination_check
from app.retrieval.nodes.retrieval import retrieve
from app.retrieval.nodes.transform_query import transform_query
from app.retrieval.state import GraphState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------

def route_after_clarification(state: GraphState) -> str:
    """
    After the clarification check, decide the next step:

    - **end**      — query is ambiguous; return options to the user.
    - **retrieve** — query is specific; proceed with the RAG pipeline.
    """
    if state.get("clarification_needed"):
        logger.info("  → Routing to END (clarification required)")
        return "end"
    logger.info("  → Routing to RETRIEVE (query is specific)")
    return "retrieve"


def decide_to_generate(state: GraphState) -> str:
    """
    After document grading, decide the next step:

    - **generate**        — at least one relevant document was found.
    - **transform_query** — no relevant docs AND retries remain.
    - **end**             — no relevant docs AND retry budget exhausted.
    """
    max_retries = getattr(settings, "MAX_QUERY_RETRIES", 3)

    if state.get("documents"):
        logger.info("  → Routing to GENERATE (relevant docs found)")
        return "generate"

    retry_count = state.get("retry_count", 0)
    if retry_count < max_retries:
        logger.info(
            "  → Routing to TRANSFORM QUERY (retry %d/%d)",
            retry_count + 1,
            max_retries,
        )
        return "transform_query"

    logger.warning("  → Routing to END (retry budget exhausted)")
    return "end"


def check_hallucination(state: GraphState) -> str:
    """
    After hallucination grading, decide the next step:

    - **end**      — answer is grounded (``hallucination_score == "yes"``).
    - **generate** — answer is hallucinated AND retries remain.
    - **end**      — answer is hallucinated but retry budget exhausted.
    """
    max_retries = getattr(settings, "MAX_QUERY_RETRIES", 3)
    score = state.get("hallucination_score", "yes")

    if score == "yes":
        logger.info("  → Routing to END (answer grounded)")
        return "end"

    retry_count = state.get("retry_count", 0)
    if retry_count < max_retries:
        logger.info("  → Routing to REGENERATE (hallucination detected)")
        return "generate"

    logger.warning(
        "  → Routing to END (hallucination detected, but retry budget exhausted)"
    )
    return "end"


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

workflow = StateGraph(GraphState)

# --- Nodes ----------------------------------------------------------------
workflow.add_node("clarification_check", clarification_check)
workflow.add_node("retrieve",            retrieve)
workflow.add_node("grade_documents",     grade_documents)
workflow.add_node("generate",            generate)
workflow.add_node("transform_query",     transform_query)
workflow.add_node("hallucination_check", hallucination_check)

# --- Edges ----------------------------------------------------------------

# Entry point: always run clarification check first
workflow.set_entry_point("clarification_check")

# clarification_check → retrieve | END
workflow.add_conditional_edges(
    "clarification_check",
    route_after_clarification,
    {
        "retrieve": "retrieve",
        "end":      END,
    },
)

# retrieve → grade_documents (always)
workflow.add_edge("retrieve", "grade_documents")

# grade_documents → generate | transform_query | END
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "generate":        "generate",
        "transform_query": "transform_query",
        "end":             END,
    },
)

# transform_query → retrieve (retry the search)
workflow.add_edge("transform_query", "retrieve")

# generate → hallucination_check (always)
workflow.add_edge("generate", "hallucination_check")

# hallucination_check → END | generate (re-generate if hallucinated)
workflow.add_conditional_edges(
    "hallucination_check",
    check_hallucination,
    {
        "end":      END,
        "generate": "generate",
    },
)

# --- Compile --------------------------------------------------------------
app_graph = workflow.compile()

logger.info("ClinIQ LangGraph compiled with 6 nodes and conditional routing (incl. clarification)")
