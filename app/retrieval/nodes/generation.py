"""
Generate node — produces a role-aware, citation-backed answer from
the filtered documents.
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
# Role-specific prompt adjustments
# ---------------------------------------------------------------------------

ROLE_INSTRUCTIONS = {
    "admin": (
        "You have full administrative access. Provide complete details."
    ),
    "doctor": (
        "You are responding to a licensed physician. Provide full clinical "
        "detail and procedure specifics."
    ),
    "nurse": (
        "You are responding to a nurse. Focus on care protocols, dosing "
        "guidelines, and patient management procedures."
    ),
    "technician": (
        "You are responding to a lab/radiology technician. Focus on "
        "technical procedures and safety protocols."
    ),
    "researcher": (
        "You are responding to a researcher. Ensure all PHI is redacted. "
        "Focus on aggregate data and policy patterns."
    ),
    "viewer": (
        "You are responding to a general staff member. Provide only "
        "high-level policy summaries."
    ),
}

RAG_TEMPLATE = """\
You are a helpful healthcare assistant for an enterprise hospital policy system.
Use the following pieces of retrieved context to answer the question.
Do not use any outside knowledge.
If the answer is not in the context, say that you don't know.

ROLE CONTEXT: {role_instruction}

IMPORTANT:
1. You must cite your sources. Use [Ref X] notation.
2. Do NOT provide medical advice. This is for policy/administrative information only.
3. Ensure no real patient PHI is generated.
4. Note which department each source comes from for transparency.

Context:
{context}

Question: {question}

Answer:"""


# ---------------------------------------------------------------------------
# Node function
# ---------------------------------------------------------------------------

def generate(state: GraphState) -> Dict[str, Any]:
    """
    Generate a role-aware, citation-backed answer from filtered documents.

    Args:
        state: The current graph state.

    Returns:
        Updated state with ``generation``.
    """
    logger.info("---GENERATE---")
    question = state["question"]
    documents = state["documents"]
    role = state.get("role", "viewer")

    if not documents:
        logger.warning("  No documents available — returning fallback answer")
        return {
            "generation": (
                "I could not find any relevant information in the "
                "policy documents you have access to."
            )
        }

    # Format context with citations
    context = ""
    for i, doc in enumerate(documents):
        citation_loc = (
            f"Page {doc.page}"
            if doc.page
            else f"Sheet {doc.metadata.get('sheet_name', 'N/A')}"
        )
        dept = doc.metadata.get("department", "unknown")
        context += (
            f"[Ref {i + 1}]: Source: {doc.source} ({dept} dept), "
            f"{citation_loc}\nContent: {doc.content}\n\n"
        )

    role_instruction = ROLE_INSTRUCTIONS.get(role, ROLE_INSTRUCTIONS["viewer"])

    prompt = ChatPromptTemplate.from_template(RAG_TEMPLATE)
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        temperature=0,
        api_key=settings.OPENAI_API_KEY,
    )

    rag_chain = prompt | llm | StrOutputParser()

    generation = rag_chain.invoke(
        {
            "context": context,
            "question": question,
            "role_instruction": role_instruction,
        }
    )

    logger.info("  Generation complete (%d chars)", len(generation))
    return {"generation": generation}
