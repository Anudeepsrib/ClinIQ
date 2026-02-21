"""
Clarification Check node — detects ambiguous clinical queries and generates
clarifying options before the expensive retrieval pipeline runs.

If the user's query is ambiguous (e.g. "tell me about the policy", "medication
info", "what are the guidelines?"), this node short-circuits the graph and
returns 2–4 specific clarifying options for the user to choose from.

This mirrors Claude's behaviour: rather than guessing or hallucinating an answer,
ClinIQ surfaces the assumption and lets the clinician guide the query.
"""

import logging
from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.retrieval.state import GraphState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured output models
# ---------------------------------------------------------------------------

class ClarificationResult(BaseModel):
    """Output of the ambiguity detector."""

    is_ambiguous: bool = Field(
        description=(
            "True if the query lacks enough specificity to retrieve a useful answer "
            "(e.g. missing department, procedure, policy name, or clinical context). "
            "False if the query is specific enough to answer directly."
        )
    )
    clarification_options: List[str] = Field(
        default_factory=list,
        description=(
            "2–4 specific, ready-to-send follow-up questions that resolve the ambiguity. "
            "Empty list if is_ambiguous is False. "
            "Each option should be a complete, standalone question a clinician would ask."
        ),
    )
    reasoning: str = Field(
        default="",
        description="Brief internal reasoning for why the query is or is not ambiguous.",
    )


# ---------------------------------------------------------------------------
# Prompt — healthcare-tuned
# ---------------------------------------------------------------------------

CLARIFICATION_SYSTEM_PROMPT = """\
You are a clinical query analyst for a hospital AI assistant called ClinIQ.

Your job: determine whether a clinician's query is specific enough to retrieve
a useful answer from hospital policy documents, or whether it's too vague and
needs clarification.

A query is AMBIGUOUS if it:
- Lacks a specific department, procedure, medication, or policy name
- Could apply to many different scenarios (e.g. "tell me about medications")
- Uses vague phrases like "the policy", "guidelines", "tell me about", "what's the rule"
- Has multiple plausible interpretations that would lead to different answers

A query is SPECIFIC enough if it:
- Names a specific procedure, medication, diagnosis code, or policy
- Specifies a clear clinical scenario (e.g. "prior auth for MRI knee", "step-down protocol for vancomycin")
- Has an unambiguous intent even without extra context

When generating clarification options:
- Make each option a COMPLETE, specific question ready to send
- Cover different plausible interpretations the clinician might have meant
- Use clinical terminology appropriate for hospital staff
- Keep options concise (under 15 words each)
- Generate 2–4 options, no more

Departments available: {departments}
User role: {role}"""

CLARIFICATION_HUMAN_PROMPT = """Query: {question}"""


# ---------------------------------------------------------------------------
# Node function
# ---------------------------------------------------------------------------

def clarification_check(state: GraphState) -> Dict[str, Any]:
    """
    Detect whether the query is ambiguous and generate clarifying options.

    Sets ``clarification_needed`` to True and populates
    ``clarification_options`` if the query is ambiguous.

    Args:
        state: The current graph state.

    Returns:
        Updated state with ``clarification_needed`` and ``clarification_options``.
    """
    logger.info("---CLARIFICATION CHECK---")

    question    = state["question"]
    departments = state.get("departments", [])
    role        = state.get("role", "viewer")

    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        temperature=0,
        api_key=settings.OPENAI_API_KEY,
    )
    structured_llm = llm.with_structured_output(ClarificationResult)

    prompt = ChatPromptTemplate.from_messages([
        ("system", CLARIFICATION_SYSTEM_PROMPT),
        ("human",  CLARIFICATION_HUMAN_PROMPT),
    ])

    chain  = prompt | structured_llm
    result = chain.invoke({
        "question":    question,
        "departments": ", ".join(departments) if departments else "all departments",
        "role":        role,
    })

    if result.is_ambiguous:
        logger.info(
            "  ⚠  Query is AMBIGUOUS — returning %d clarification options",
            len(result.clarification_options),
        )
        logger.debug("  Reasoning: %s", result.reasoning)
    else:
        logger.info("  ✓ Query is SPECIFIC — proceeding to retrieval")

    return {
        "clarification_needed":  result.is_ambiguous,
        "clarification_options": result.clarification_options,
    }
