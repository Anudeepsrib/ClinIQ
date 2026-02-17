"""
Document Grader node — checks if retrieved medical documents are relevant
to the user's question before passing them to the generation step.
"""

import logging
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.retrieval.state import GraphState
from app.schemas.models import RetrievalResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured output model
# ---------------------------------------------------------------------------

class GradeDocuments(BaseModel):
    """Binary relevance score for a retrieved document."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'",
    )


# ---------------------------------------------------------------------------
# Grading prompt — healthcare-tuned
# ---------------------------------------------------------------------------

GRADER_SYSTEM_PROMPT = """\
You are a clinical document relevance grader for a hospital knowledge system.

Given a user question and a retrieved document, determine if the document
is relevant to answering the question.

Relevance criteria:
- The document contains keywords or semantic meaning related to the question.
- Clinical terminology, procedure codes (ICD/CPT), drug names, or dosing
  guidelines that match the clinical intent of the question count as relevant.
- Policy documents that address the department or topic in the question are
  relevant even if they use different phrasing.

Give a binary score: 'yes' if the document is relevant, 'no' otherwise.
Do NOT be overly strict — partial relevance is acceptable."""

GRADER_HUMAN_PROMPT = (
    "Retrieved document:\n\n{document}\n\nUser question: {question}"
)


# ---------------------------------------------------------------------------
# Node function
# ---------------------------------------------------------------------------

def grade_documents(state: GraphState) -> Dict[str, Any]:
    """
    Determines whether retrieved documents are relevant to the question.

    Filters out irrelevant documents so only clinically relevant context
    is passed to the generation step.

    Args:
        state: The current graph state.

    Returns:
        Updated state with only relevant documents.
    """
    logger.info("---CHECK DOCUMENT RELEVANCE---")
    question = state["question"]
    documents = state["documents"]

    # LLM with structured output
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        temperature=0,
        api_key=settings.OPENAI_API_KEY,
    )
    structured_llm_grader = llm.with_structured_output(GradeDocuments)

    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", GRADER_SYSTEM_PROMPT),
            ("human", GRADER_HUMAN_PROMPT),
        ]
    )

    retrieval_grader = grade_prompt | structured_llm_grader

    filtered_docs: list[RetrievalResult] = []
    for doc in documents:
        score = retrieval_grader.invoke(
            {"question": question, "document": doc.content}
        )
        grade = score.binary_score

        if grade.lower() == "yes":
            logger.info("  ✓ GRADE: DOCUMENT RELEVANT — %s", doc.source)
            filtered_docs.append(doc)
        else:
            logger.info("  ✗ GRADE: DOCUMENT NOT RELEVANT — %s", doc.source)

    logger.info(
        "  Kept %d / %d documents after grading", len(filtered_docs), len(documents)
    )
    return {"documents": filtered_docs, "question": question}
