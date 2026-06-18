"""
Clinical intelligence API router — Quick-help medical intelligence for staff.

Exposes a POST endpoint that allows doctors and nurses to get fast,
evidence-based answers to clinical questions through the ClinIQ interface,
powered by the configured Gemma/OpenAI provider.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.chat.copilot_service import copilot_health_service
from app.core.limiter import limiter
from app.core.logging import redact_text
from app.schemas.copilot_models import CopilotHelpRequest, CopilotHelpResponse
from app.security.rbac import require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/copilot", tags=["Clinical Intelligence"])
NurseUser = Annotated[dict, Depends(require_role("nurse"))]


@router.post("/quick-help", response_model=CopilotHelpResponse)
@limiter.limit("20/minute")
async def copilot_quick_help(
    request: Request,
    body: CopilotHelpRequest,
    user: NurseUser,  # nurse-level and above (nurse, doctor, admin)
):
    """
    Get quick medical intelligence from the configured provider.

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
        logger.exception("Clinical intelligence error: %s", redact_text(e))
        raise HTTPException(
            status_code=500,
            detail="Clinical intelligence service unavailable",
        ) from e
