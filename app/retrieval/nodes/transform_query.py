"""
Query Transformer node — rewrites the user's question to improve retrieval
recall when the initial search returns no relevant documents.

Healthcare-aware: expands medical abbreviations, adds clinical synonyms,
and tracks every rewrite in the audit trail.
"""

import logging
from typing import Any, Dict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.retrieval.state import GraphState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rewrite prompt — healthcare-aware
# ---------------------------------------------------------------------------

REWRITE_SYSTEM_PROMPT = """\
You are a medical query optimizer for a hospital knowledge retrieval system.

The user's original question did not return relevant documents.  Your job
is to rewrite the question to improve search recall.

Strategies:
1. Expand medical abbreviations (e.g. "BP" → "blood pressure").
2. Add clinical synonyms (e.g. "heart attack" ↔ "myocardial infarction").
3. Broaden overly specific queries while keeping clinical intent.
4. Include related procedure codes or drug class names when appropriate.
5. Rephrase for clarity without changing the meaning.

Return ONLY the rewritten question — no explanation or preamble."""

REWRITE_HUMAN_PROMPT = "Original question: {question}"


# ---------------------------------------------------------------------------
# Node function
# ---------------------------------------------------------------------------

def transform_query(state: GraphState) -> Dict[str, Any]:
    """
    Rewrite the user question to improve retrieval recall.

    Increments ``retry_count`` and appends the rewrite to
    ``query_transformations`` for audit purposes.

    Args:
        state: The current graph state.

    Returns:
        Updated state with rewritten ``question``, incremented
        ``retry_count``, and updated ``query_transformations``.
    """
    logger.info("---TRANSFORM QUERY---")
    original_question = state["question"]
    retry_count = state.get("retry_count", 0)
    transformations = list(state.get("query_transformations", []))

    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        temperature=0.4,  # slight creativity for synonyms
        api_key=settings.OPENAI_API_KEY,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", REWRITE_SYSTEM_PROMPT),
            ("human", REWRITE_HUMAN_PROMPT),
        ]
    )

    chain = prompt | llm | StrOutputParser()

    rewritten = chain.invoke({"question": original_question})
    rewritten = rewritten.strip()

    retry_count += 1
    transformations.append(rewritten)

    logger.info("  Retry #%d: '%s' → '%s'", retry_count, original_question, rewritten)

    return {
        "question": rewritten,
        "retry_count": retry_count,
        "query_transformations": transformations,
    }
