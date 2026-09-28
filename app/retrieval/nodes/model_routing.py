"""LangGraph node for safe, fail-open model routing."""

from __future__ import annotations

import logging
from typing import Any

from app.chat.llm_provider import model_for_provider
from app.core.config import settings
from app.retrieval.state import GraphState
from app.routing.jev_router import RoutingDecision, classify_routing_context
from app.routing.model_profiles import resolve_model_profile
from app.security.pii import pii_manager

logger = logging.getLogger(__name__)


def build_safe_routing_context(state: GraphState) -> dict[str, Any]:
    """Return the exact allowlisted, re-sanitized payload permitted to leave ClinIQ."""
    return {
        "question": pii_manager.anonymize(state["question"]),
        "role": state.get("role", "viewer"),
        "departments": list(state.get("departments", [])),
        "query_modality": state.get("query_modality", "text"),
    }


def _apply_safety_overrides(decision: RoutingDecision, context: dict[str, Any]) -> RoutingDecision:
    question = context["question"].lower()
    high_stakes = float(decision.signals.get("high_stakes", 0.0))
    comparison = any(term in question for term in ("compare", "difference", "conflict"))
    synthesis = any(term in question for term in ("across", "synthesi", "between"))
    multi_department = len(context["departments"]) > 1 and synthesis

    if high_stakes >= settings.JEV_HIGH_STAKES_THRESHOLD or comparison or multi_department:
        return RoutingDecision("powerful", decision.confidence, decision.signals)
    if decision.confidence < settings.JEV_MIN_CONFIDENCE:
        return RoutingDecision(
            "standard", decision.confidence, decision.signals, True, "low_confidence"
        )
    return decision


async def route_model(state: GraphState) -> dict[str, Any]:
    """Resolve provider precedence and optionally make one sanitized Jev call."""
    mode = settings.MODEL_ROUTING_MODE if settings.MODEL_ROUTING_ENABLED else "disabled"
    requested = state.get("model_mode", "auto")
    provider_override = bool(state.get("provider_override"))
    current_provider = state.get("llm_provider") or settings.LLM_PROVIDER

    if provider_override or mode == "disabled":
        return {
            "model_route": settings.MODEL_ROUTE_DEFAULT,
            "routing_confidence": 1.0 if provider_override else 0.0,
            "routing_signals": {"source": "provider_override" if provider_override else "disabled"},
            "routing_fallback": False,
            "generation_provider": current_provider,
            "generation_model": model_for_provider(current_provider),
        }

    if requested in {"fast", "standard", "powerful"}:
        decision = RoutingDecision(requested, 1.0, {"source": "manual_profile"})
    else:
        context = build_safe_routing_context(state)
        decision = _apply_safety_overrides(await classify_routing_context(context), context)

    profile = resolve_model_profile(decision.model_route)
    active_profile = requested != "auto" or mode == "active"
    generation_provider = profile.provider if active_profile else current_provider
    generation_model = profile.model if active_profile else model_for_provider(current_provider)
    metadata = dict(state.get("metadata", {}))
    metadata.update(
        {
            "router": "jev" if requested == "auto" else "manual",
            "routing_mode": mode,
            "model_route": decision.model_route,
            "routing_confidence": decision.confidence,
            "routing_fallback": decision.fallback,
            "generation_provider": generation_provider,
            "generation_model": generation_model,
        }
    )
    if decision.fallback:
        logger.warning(
            "MODEL ROUTER: fallback → standard reason=%s", decision.fallback_reason
        )
    else:
        logger.info(
            "MODEL ROUTER: %s → %s confidence=%.2f",
            mode,
            decision.model_route,
            decision.confidence,
        )
    return {
        "model_route": decision.model_route,
        "routing_confidence": decision.confidence,
        "routing_signals": decision.signals,
        "routing_fallback": decision.fallback,
        "generation_provider": generation_provider,
        "generation_model": generation_model,
        "metadata": metadata,
    }
