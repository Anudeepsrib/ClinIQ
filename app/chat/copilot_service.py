"""Policy quick-help service for bounded staff reference lookups."""

import logging
from typing import Optional

import httpx

from app.core.logging import redact_text
from app.schemas.copilot_models import CopilotHelpRequest, CopilotHelpResponse, CopilotSource
from app.security.pii import pii_manager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt for concise, source-aware policy reference answers.
# ---------------------------------------------------------------------------
COPILOT_HEALTH_SYSTEM_PROMPT = (
    "You are a policy quick-help assistant integrated into the ClinIQ hospital system. "
    "Your role is to provide concise reference-grade answers about institutional "
    "policies, procedures, documentation requirements, coverage tables, and escalation paths. "
    "You must:\n"
    "1. Use supplied policy context when present and cite source titles when possible.\n"
    "2. State when the available context is insufficient.\n"
    "3. Never provide diagnosis, treatment, legal advice, or compliance certification.\n"
    "4. Prioritize policy requirements, approval paths, documentation steps, and role boundaries.\n"
    "5. Always include a safety disclaimer.\n"
    "Format responses concisely for quick scanning by hospital staff."
)


class CopilotHealthService:
    """Async service wrapping the configured policy reference provider."""

    def __init__(self):
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def get_quick_help(
        self,
        request: CopilotHelpRequest,
        user_role: str,
        user_id: str,
    ) -> CopilotHelpResponse:
        """
        Query the configured provider for quick policy reference help.
        Routes between hosted Gemma 4, Azure/OpenAI, and local Gemma 4 providers.
        """
        try:
            answer, sources = await self._call_copilot_api(
                question=request.question,
                context=request.context,
                department=request.department,
                user_role=user_role,
                images=request.images,
                provider=request.provider,
            )

            confidence = self._assess_confidence(answer)

            return CopilotHelpResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
            )

        except Exception as e:
            logger.error("Policy quick-help service error: %s", redact_text(e))
            return CopilotHelpResponse(
                answer=(
                    "I'm currently unable to reach the policy quick-help service. "
                    "Please try again shortly or consult your department's reference materials."
                ),
                sources=[],
                confidence="low",
            )

    async def _call_copilot_api(
        self,
        question: str,
        context: Optional[str],
        department: Optional[str],
        user_role: str,
        images: Optional[list[str]] = None,
        provider: Optional[str] = None,
    ) -> tuple[str, list[CopilotSource]]:
        """
        Call the underlying AI service for policy reference help.
        Supports hosted Google Gemma 4, Azure/OpenAI, and local Gemma 4.
        """
        from app.chat.llm_provider import (
            generate_chat_response,
            is_local_llm_provider,
            provider_display_name,
            resolve_llm_provider,
        )

        # Prioritize request-level provider override, fallback to global settings
        active_provider = resolve_llm_provider(provider)

        safe_question = pii_manager.anonymize(question)
        safe_context = pii_manager.anonymize(context) if context else None

        user_prompt = safe_question
        if safe_context:
            user_prompt = f"Policy context: {safe_context}\n\nQuestion: {safe_question}"
        if department:
            user_prompt += f"\n\n(Department: {department}, Role: {user_role})"

        if is_local_llm_provider(active_provider):
            from app.chat.local_llm_adapter import local_llm_adapter
            
            answer = await local_llm_adapter.generate_response(
                prompt=user_prompt,
                system_prompt=COPILOT_HEALTH_SYSTEM_PROMPT,
                images=images,
                provider=active_provider,
            )
            
            sources = [
                CopilotSource(
                    title=f"Gemma 4 ({active_provider.upper()}) - Local Policy Reference",
                    url="http://localhost",
                    provider=provider_display_name(active_provider),
                )
            ]
        else:
            answer = await generate_chat_response(
                prompt=user_prompt,
                system_prompt=COPILOT_HEALTH_SYSTEM_PROMPT,
                provider=active_provider,
                images=images,
                temperature=0.2,
                max_tokens=1024,
            )
            
            sources = [
                CopilotSource(
                    title=f"{provider_display_name(active_provider)} - Policy Reference",
                    url="https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api"
                    if active_provider == "google_gemma"
                    else "https://platform.openai.com/docs/models",
                    provider=provider_display_name(active_provider),
                )
            ]

        return answer, sources

    @staticmethod
    def _assess_confidence(answer: str) -> str:
        """Simple heuristic confidence assessment."""
        hedging_phrases = [
            "i'm not sure", "it is unclear", "consult a specialist",
            "insufficient information", "further evaluation needed",
            "cannot determine", "seek immediate",
        ]
        lower = answer.lower()
        hedge_count = sum(1 for phrase in hedging_phrases if phrase in lower)

        if hedge_count >= 2:
            return "low"
        elif hedge_count == 1:
            return "medium"
        return "high"

    async def close(self):
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.close()


# Module-level singleton
copilot_health_service = CopilotHealthService()
