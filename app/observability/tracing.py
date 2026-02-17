"""
LangSmith observability helpers for ClinIQ.

Provides:
- ``build_langsmith_config``  — creates a ``RunnableConfig`` with custom
  metadata and tags so hospital admins can filter traces by department,
  role, and user in the LangSmith dashboard.
- ``get_langsmith_client``    — lazy singleton for the LangSmith SDK client.
- ``create_feedback``         — wraps ``client.create_feedback()`` for
  clinician correction / feedback loops.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy singleton
# ---------------------------------------------------------------------------

_langsmith_client = None


def get_langsmith_client():
    """Return a shared ``langsmith.Client`` instance (lazy-init)."""
    global _langsmith_client  # noqa: PLW0603
    if _langsmith_client is None:
        try:
            from langsmith import Client

            _langsmith_client = Client()
            logger.info("LangSmith client initialised (project=%s)", settings.LANGCHAIN_PROJECT)
        except Exception as exc:
            logger.warning("LangSmith client unavailable: %s", exc)
    return _langsmith_client


# ---------------------------------------------------------------------------
# Config builder
# ---------------------------------------------------------------------------

def build_langsmith_config(
    *,
    user_id: str,
    role: str,
    departments: List[str],
    extra_metadata: Optional[Dict[str, Any]] = None,
    extra_tags: Optional[List[str]] = None,
) -> RunnableConfig:
    """
    Build a ``RunnableConfig`` with LangSmith metadata and tags.

    This config is passed to ``app_graph.ainvoke(inputs, config=config)``
    so that every LLM call, retriever call, and node execution within the
    graph run is annotated with hospital-specific context.

    Hospital admins can then filter traces in the LangSmith UI by:
    - **department** (e.g. ``radiology``, ``pharmacy``)
    - **user_role** (e.g. ``doctor``, ``nurse``)
    - **user_id** (specific staff member)

    Args:
        user_id:        Username of the requester.
        role:           User role (``doctor``, ``nurse``, etc.).
        departments:    Departments included in the search scope.
        extra_metadata: Optional additional key-value pairs.
        extra_tags:     Optional additional string tags.

    Returns:
        A ``RunnableConfig`` ready to pass to LangGraph.
    """
    metadata: Dict[str, Any] = {
        "user_id": user_id,
        "user_role": role,
        "departments": departments,
        "project": settings.LANGCHAIN_PROJECT,
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    tags: List[str] = [
        f"role:{role}",
        f"user:{user_id}",
        *(f"dept:{d}" for d in departments),
    ]
    if extra_tags:
        tags.extend(extra_tags)

    config: RunnableConfig = {
        "metadata": metadata,
        "tags": tags,
        "run_name": f"ClinIQ query — {role}@{','.join(departments)}",
    }

    logger.debug("LangSmith config: tags=%s", tags)
    return config


# ---------------------------------------------------------------------------
# Feedback loop
# ---------------------------------------------------------------------------

def create_feedback(
    run_id: str,
    key: str,
    score: float,
    comment: Optional[str] = None,
) -> bool:
    """
    Submit clinician feedback to LangSmith for a specific run.

    This is the **Gold Standard** for healthcare AI observability: when a
    doctor or nurse corrects the chatbot, the correction is recorded
    against the original trace so the team can measure accuracy over time.

    Args:
        run_id:  The LangSmith run ID (returned in the query response).
        key:     Feedback dimension, e.g. ``"correctness"``, ``"relevance"``.
        score:   Numeric score (0.0–1.0).
        comment: Optional free-text explanation.

    Returns:
        ``True`` if the feedback was recorded successfully.
    """
    client = get_langsmith_client()
    if client is None:
        logger.warning("Cannot record feedback — LangSmith client unavailable")
        return False

    try:
        client.create_feedback(
            run_id=run_id,
            key=key,
            score=score,
            comment=comment,
        )
        logger.info(
            "Feedback recorded: run=%s key=%s score=%.2f", run_id, key, score
        )
        return True
    except Exception as exc:
        logger.error("Failed to record feedback: %s", exc)
        return False
