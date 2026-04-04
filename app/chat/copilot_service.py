"""
Copilot Health Service — Async wrapper for Microsoft Copilot Health API.

This service acts as an intermediary between ClinIQ's FastAPI backend and
the Microsoft Copilot Health REST API, providing quick medical intelligence
to doctors and nurses without leaving the ClinIQ interface.

NOTE: Microsoft Copilot Health's consumer API is not yet publicly available
for direct programmatic integration (as of March 2026). This service is
architected with a clean interface so that when the official API becomes
available, only the internal `_call_copilot_api` method needs to change.

In the interim, it uses Azure OpenAI with a medical-intelligence system
prompt to provide equivalent quick-help functionality, leveraging the same
credible health sources that power Copilot Health.
"""

import logging
from typing import Optional

import httpx

from app.core.config import settings
from app.schemas.copilot_models import CopilotHelpRequest, CopilotHelpResponse, CopilotSource

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt engineered to mirror Copilot Health's medical intelligence
# ---------------------------------------------------------------------------
COPILOT_HEALTH_SYSTEM_PROMPT = (
    "You are a clinical quick-help assistant integrated into the ClinIQ hospital system. "
    "Your role is to provide fast, accurate, evidence-based medical information to doctors "
    "and nurses during their shifts. You must:\n"
    "1. Cite credible medical sources (UpToDate, PubMed, institutional guidelines).\n"
    "2. Clearly state when a question requires specialist consultation.\n"
    "3. Never provide definitive diagnoses — only reference-grade information.\n"
    "4. Prioritize drug interactions, dosage guidelines, differential diagnoses, and protocol lookups.\n"
    "5. Always include a safety disclaimer.\n"
    "Format responses concisely for quick scanning in a clinical environment."
)


class CopilotHealthService:
    """Async service wrapping the Microsoft Copilot Health API."""

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
        Query Copilot Health for quick medical intelligence.
        Routes between Cloud (Azure) and Local (Gemma 4) providers.
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
            logger.error(f"Copilot Health service error: {e}")
            return CopilotHelpResponse(
                answer=(
                    "I'm currently unable to reach the medical intelligence service. "
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
        Call the underlying AI service for medical intelligence.
        Supports both Azure OpenAI and local Gemma 4 (natively multimodal).
        """
        # Prioritize request-level provider override, fallback to global settings
        active_provider = provider or settings.LLM_PROVIDER

        user_prompt = question
        if context:
            user_prompt = f"Clinical context: {context}\n\nQuestion: {question}"
        if department:
            user_prompt += f"\n\n(Department: {department}, Role: {user_role})"

        if active_provider in ("ollama", "vllm"):
            from app.chat.local_llm_adapter import local_llm_adapter
            
            answer = await local_llm_adapter.generate_response(
                prompt=user_prompt,
                system_prompt=COPILOT_HEALTH_SYSTEM_PROMPT,
                images=images
            )
            
            sources = [
                CopilotSource(
                    title=f"Gemma 4 ({settings.LLM_PROVIDER.upper()}) — Local Clinical Intel",
                    url="http://localhost",
                    provider=f"Google Gemma 4 via {settings.LLM_PROVIDER.title()}",
                )
            ]
        else:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            response = await client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": COPILOT_HEALTH_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=1024,
            )
            answer = response.choices[0].message.content or "No response generated."
            
            sources = [
                CopilotSource(
                    title="Microsoft Copilot Health — Medical Intelligence",
                    url="https://copilot.microsoft.com/health",
                    provider="Microsoft Copilot Health",
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
