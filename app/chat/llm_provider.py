"""Provider selection helpers for ClinIQ language-model calls."""

from __future__ import annotations

from typing import Any, Optional
from urllib.parse import urlparse

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings

VALID_LLM_PROVIDERS = {"google_gemma", "azure_openai", "ollama", "vllm"}
LOCAL_LLM_PROVIDERS = {"ollama", "vllm"}


def resolve_llm_provider(provider: Optional[str] = None) -> str:
    """Return the requested provider, falling back to global settings."""
    active_provider = (provider or settings.LLM_PROVIDER).strip()
    if active_provider not in VALID_LLM_PROVIDERS:
        raise ValueError(
            "Unsupported LLM provider. Expected one of: "
            f"{', '.join(sorted(VALID_LLM_PROVIDERS))}."
        )
    return active_provider


def is_local_llm_provider(provider: Optional[str] = None) -> bool:
    return resolve_llm_provider(provider) in LOCAL_LLM_PROVIDERS


def is_llm_configured(provider: Optional[str] = None) -> bool:
    """Return whether the selected provider has enough configuration to be called."""
    active_provider = resolve_llm_provider(provider)
    if active_provider == "google_gemma":
        return bool(settings.GOOGLE_API_KEY)
    if active_provider == "azure_openai":
        return bool(settings.OPENAI_API_KEY)
    return True


def missing_llm_configuration_message(provider: Optional[str] = None) -> str:
    active_provider = resolve_llm_provider(provider)
    if active_provider == "google_gemma":
        return "GOOGLE_API_KEY missing"
    if active_provider == "azure_openai":
        return "OPENAI_API_KEY missing"
    return f"{active_provider} local model server unavailable"


def provider_display_name(provider: Optional[str] = None) -> str:
    active_provider = resolve_llm_provider(provider)
    labels = {
        "google_gemma": "Google Gemma 4",
        "azure_openai": "Azure/OpenAI",
        "ollama": "Google Gemma 4 via Ollama",
        "vllm": "Google Gemma 4 via vLLM",
    }
    return labels[active_provider]


def model_for_provider(provider: Optional[str] = None) -> str:
    """Resolve the model name for the requested provider."""
    active_provider = resolve_llm_provider(provider)
    if active_provider in LOCAL_LLM_PROVIDERS:
        return settings.LOCAL_LLM_MODEL
    if active_provider == settings.LLM_PROVIDER:
        return settings.LLM_MODEL
    if active_provider == "google_gemma":
        return settings.GOOGLE_GEMMA_MODEL
    if active_provider == "azure_openai":
        return settings.OPENAI_LLM_MODEL
    return settings.LLM_MODEL


def _validate_localhost(url: str) -> None:
    parsed = urlparse(url)
    hostname = parsed.hostname
    if hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError(
            "Security Violation: Local LLM traffic must be restricted to localhost. "
            f"Attempted to connect to: {hostname}"
        )


def _openai_compatible_base_url(base_url: str) -> str:
    _validate_localhost(base_url)
    return f"{base_url.rstrip('/')}/v1"


def get_chat_model(
    *,
    provider: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: Optional[int] = None,
) -> BaseChatModel:
    """Build the configured chat model for RAG and clinical quick-help calls."""
    active_provider = resolve_llm_provider(provider)

    if active_provider == "google_gemma":
        from langchain_google_genai import ChatGoogleGenerativeAI

        kwargs: dict[str, Any] = {
            "model": model_for_provider(active_provider),
            "temperature": temperature,
            "api_key": settings.GOOGLE_API_KEY,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if settings.GEMMA_THINKING_LEVEL:
            kwargs["thinking_level"] = settings.GEMMA_THINKING_LEVEL
        return ChatGoogleGenerativeAI(**kwargs)

    if active_provider == "azure_openai":
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": model_for_provider(active_provider),
            "temperature": temperature,
            "api_key": settings.OPENAI_API_KEY,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        return ChatOpenAI(**kwargs)

    from langchain_openai import ChatOpenAI

    base_url = (
        _openai_compatible_base_url(settings.OLLAMA_BASE_URL)
        if active_provider == "ollama"
        else _openai_compatible_base_url(settings.VLLM_BASE_URL)
    )
    kwargs = {
        "model": model_for_provider(active_provider),
        "temperature": temperature,
        "base_url": base_url,
        "api_key": "local",
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    return ChatOpenAI(**kwargs)


def build_human_content(prompt: str, images: Optional[list[str]] = None) -> Any:
    """Build LangChain multimodal content from a prompt and optional base64 images."""
    if not images:
        return prompt

    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for image in images:
        image_url = image if image.startswith("data:") else f"data:image/jpeg;base64,{image}"
        content.append({"type": "image_url", "image_url": {"url": image_url}})
    return content


async def generate_chat_response(
    *,
    prompt: str,
    system_prompt: str,
    provider: Optional[str] = None,
    images: Optional[list[str]] = None,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> str:
    """Call the selected hosted or OpenAI-compatible chat provider."""
    llm = get_chat_model(
        provider=provider,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    response = await llm.ainvoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=build_human_content(prompt, images)),
        ]
    )

    content = response.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and isinstance(part.get("text"), str):
                parts.append(part["text"])
        return "\n".join(parts).strip()
    return str(content)
