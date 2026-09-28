"""Central route/profile to provider/model configuration."""

from dataclasses import dataclass
from typing import Literal

from app.core.config import settings

ModelRoute = Literal["fast", "standard", "powerful"]
VALID_MODEL_ROUTES = {"fast", "standard", "powerful"}


@dataclass(frozen=True)
class ModelProfile:
    name: ModelRoute
    provider: str
    model: str
    temperature: float = 0.0
    max_tokens: int | None = None


def resolve_model_profile(route: str) -> ModelProfile:
    """Resolve a route centrally, inheriting unset values from legacy settings."""
    if route not in VALID_MODEL_ROUTES:
        raise ValueError(f"Unsupported model route: {route}")
    prefix = f"MODEL_ROUTE_{route.upper()}"
    provider = getattr(settings, f"{prefix}_PROVIDER") or settings.LLM_PROVIDER
    model = getattr(settings, f"{prefix}_MODEL") or _legacy_model(provider)
    return ModelProfile(name=route, provider=provider, model=model)


def _legacy_model(provider: str) -> str:
    if provider in {"ollama", "vllm"}:
        return settings.LOCAL_LLM_MODEL
    if provider == "google_gemma":
        return settings.GOOGLE_GEMMA_MODEL
    if provider == "azure_openai":
        return settings.OPENAI_LLM_MODEL
    return settings.LLM_MODEL
