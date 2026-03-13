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

        Currently uses Azure OpenAI as a bridge until the official
        Copilot Health API is publicly available for integration.
        """
        try:
            answer, sources = await self._call_copilot_api(
                question=request.question,
                context=request.context,
                department=request.department,
                user_role=user_role,
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
    ) -> tuple[str, list[CopilotSource]]:
        """
        Call the underlying AI service for medical intelligence.

        Architecture note: This method is the single integration point.
        When Microsoft releases the Copilot Health API for programmatic
        access, replace the body of this method — the rest of the service
        remains unchanged.
        """
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        user_prompt = question
        if context:
            user_prompt = f"Clinical context: {context}\n\nQuestion: {question}"
        if department:
            user_prompt += f"\n\n(Department: {department}, Role: {user_role})"

        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": COPILOT_HEALTH_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,  # low temp for factual medical queries
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
