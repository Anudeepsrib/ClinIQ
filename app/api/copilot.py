"""
Copilot Health API router — Quick-help medical intelligence for clinical staff.

Exposes a POST endpoint that allows doctors and nurses to get fast,
evidence-based answers to clinical questions through the ClinIQ interface,
powered by Microsoft Copilot Health (bridged via Azure OpenAI).
"""

from fastapi import APIRouter, Depends, HTTPException, Request

from app.schemas.copilot_models import CopilotHelpRequest, CopilotHelpResponse
from app.security.rbac import get_current_user, require_role
from app.chat.copilot_service import copilot_health_service
from app.core.limiter import limiter

router = APIRouter(prefix="/copilot", tags=["Copilot Health"])


@router.post("/quick-help", response_model=CopilotHelpResponse)
@limiter.limit("20/minute")
async def copilot_quick_help(
    request: Request,
    body: CopilotHelpRequest,
    user: dict = Depends(require_role("nurse")),  # nurse-level and above (nurse, doctor, admin)
):
    """
    Get quick medical intelligence from Copilot Health.

    Accessible to nurses, doctors, and admins. Returns evidence-based
    clinical information with source citations and a safety disclaimer.
    """
    try:
        response = await copilot_health_service.get_quick_help(
            request=body,
            user_role=user["role"],
            user_id=user["username"],
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot Health error: {e}")
