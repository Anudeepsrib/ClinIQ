"""
Hallucination Grader node — verifies that the generated answer is fully
grounded in the retrieved clinical context.

If the answer contains claims not supported by the documents, this node
flags it so the graph can route back to regeneration.
"""

import logging
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.chat.llm_provider import (
    get_chat_model,
    is_llm_configured,
    missing_llm_configuration_message,
)
from app.core.config import settings
from app.retrieval.state import GraphState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured output model
# ---------------------------------------------------------------------------

class GradeHallucination(BaseModel):
    """Binary score for hallucination check."""

    binary_score: str = Field(
        description=(
            "'yes' if the answer is fully grounded in the provided documents, "
            "'no' if it contains unsupported claims"
        ),
    )


# ---------------------------------------------------------------------------
# Hallucination-check prompt — healthcare-tuned
# ---------------------------------------------------------------------------

HALLUCINATION_SYSTEM_PROMPT = """\
You are a clinical accuracy auditor for a hospital AI system.

You will be given:
1. A set of retrieved medical/policy documents (the FACTS).
2. An AI-generated answer.

Your task: determine if the answer is fully grounded in the FACTS.

Rules:
- Every factual claim in the answer MUST be supported by the documents.
- Medical dosages, procedure steps, drug interactions, and policy details
  must exactly match what the documents state.
- Generic transitional phrases ("Based on the documents…") are acceptable.
- If the answer adds ANY clinical detail not present in the documents,
  score 'no'.

Return 'yes' if grounded, 'no' if hallucinated."""

HALLUCINATION_HUMAN_PROMPT = """\
Retrieved documents (FACTS):

{documents}

---

AI-generated answer:

{generation}"""


# ---------------------------------------------------------------------------
# Node function
# ---------------------------------------------------------------------------

def hallucination_check(state: GraphState) -> Dict[str, Any]:
    """
    Check whether the generated answer is grounded in the retrieved context.

    Sets ``hallucination_score`` to ``"yes"`` (grounded) or ``"no"``
    (hallucinated) so the graph can decide whether to accept or retry.

    Args:
        state: The current graph state.

    Returns:
        Updated state with ``hallucination_score``.
    """
    logger.info("---HALLUCINATION CHECK---")
    documents = state["documents"]
    generation = state.get("generation", "")
    max_retries = getattr(settings, "MAX_QUERY_RETRIES", 3)
    llm_provider = state.get("llm_provider")

    if not generation:
        logger.warning("  No generation to check — failing closed")
        return {
            "hallucination_score": "no",
            "generation": "I could not verify an answer against retrieved documents.",
            "retry_count": max_retries,
        }

    if not documents:
        logger.warning("  No documents available for hallucination grading — failing closed")
        return {
            "hallucination_score": "no",
            "generation": "I could not verify an answer because no supporting documents were retrieved.",
            "retry_count": max_retries,
        }

    if not is_llm_configured(llm_provider):
        logger.warning(
            "%s — accepting extractive fallback as grounded",
            missing_llm_configuration_message(llm_provider),
        )
        return {"hallucination_score": "yes"}

    # Format documents into a single text block
    docs_text = "\n\n".join(
        f"[Doc {i + 1}] ({doc.source}): {doc.content}"
        for i, doc in enumerate(documents)
    )

    llm = get_chat_model(provider=llm_provider, temperature=0)
    structured_llm = llm.with_structured_output(GradeHallucination)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", HALLUCINATION_SYSTEM_PROMPT),
            ("human", HALLUCINATION_HUMAN_PROMPT),
        ]
    )

    chain = prompt | structured_llm

    try:
        result = chain.invoke({"documents": docs_text, "generation": generation})
        score = result.binary_score.lower()
    except Exception as exc:
        logger.error("Hallucination grader failed closed: %s", exc)
        return {
            "hallucination_score": "no",
            "generation": "I could not verify this answer against the retrieved documents.",
            "retry_count": max_retries,
        }

    if score == "yes":
        logger.info("  ✓ Answer is GROUNDED in retrieved context")
    else:
        logger.warning("  ✗ Answer may contain HALLUCINATED content")
        if state.get("retry_count", 0) >= max_retries:
            return {
                "hallucination_score": "no",
                "generation": "I could not verify this answer against the retrieved documents.",
            }

    return {"hallucination_score": score}
