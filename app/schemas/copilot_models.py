"""Pydantic models for the Copilot Health quick-help integration."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CopilotHelpRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The clinical question to ask Copilot Health")
    context: Optional[str] = None  # optional patient/clinical context
    department: Optional[str] = None


class CopilotSource(BaseModel):
    title: str
    url: Optional[str] = None
    provider: str = "Microsoft Copilot Health"


class CopilotHelpResponse(BaseModel):
    answer: str
    sources: List[CopilotSource] = []
    confidence: str = "medium"  # "high" | "medium" | "low"
    disclaimer: str = (
        "This information is provided by Microsoft Copilot Health for reference only. "
        "Always verify with institutional protocols and clinical judgement."
    )
    response_type: str = "copilot_health"
