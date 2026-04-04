# Copilot Health Backend Integration Plan

## Overview
The goal is to integrate Microsoft's newly announced "Copilot Health" into ClinIQ's backend. The integration will serve as a "quick help" medical intelligence layer for doctors and nurses. Crucially, the UI will remain exactly the same (the Asymmetric 80/20 Clinical Grid). The integration will exist purely in the FastAPI backend as a service, allowing ClinIQ to act as a one-stop solution.

## Project Type
**BACKEND**

## Success Criteria
- **Functional**: The FastAPI backend can securely query the Copilot Health API (or Azure Health equivalent wrapper) for quick medical intelligence.
- **Immutable UI**: No changes to the Next.js visual components. The frontend will only route requests differently under the hood using `chatStore.ts` if needed.
- **Security Check**: PHI masking and JWT Role-based Access Control (Admin → Doctor → Nurse) remain intact. 

## Tech Stack
- **Backend:** Python 3.10+, FastAPI
- **AI Integration:** LangGraph/LangChain, Microsoft Health APIs (REST)

## File Structure
```text
enterprise-healthcare-rag/
├── app/
│   ├── api/
│   │   ├── [MODIFY] routes.py               # Register new copilot router
│   │   ├── [NEW] copilot.py                 # New router for Copilot Health
│   ├── chat/
│   │   ├── [NEW] copilot_service.py         # Service wrapper for Copilot Health API
│   ├── schemas/
│   │   ├── [NEW] copilot_models.py          # Pydantic models for Copilot Health
├── main.py                                  # (Already correct, but good to know)
├── frontend/
│   ├── src/store/
│   │   ├── [MODIFY] chatStore.ts            # Adjust payload/endpoints to support the quick-help route
```

## Task Breakdown

### Task 1: Define Copilot Health Schemas
- **Agent**: `backend-specialist`
- **Skill**: `clean-code`
- **Priority**: P0
- **INPUT**: Requirement for "Quick Help" response
- **OUTPUT**: `app/schemas/copilot_models.py` with `CopilotHelpRequest` and `CopilotHelpResponse`.
- **VERIFY**: Ensure models align with existing `QueryRequest/Response` patterns.

### Task 2: Implement Copilot Health Service Wrapper
- **Agent**: `backend-specialist`
- **Skill**: `api-patterns`
- **Priority**: P0
- **Dependencies**: Task 1
- **INPUT**: Microsoft Copilot Health REST API concepts
- **OUTPUT**: `app/chat/copilot_service.py` with an async `CopilotHealthService` class.
- **VERIFY**: Unit test verifying the service returns valid medical intelligence (mocked for now).

### Task 3: Create FastAPI Quick-Help Endpoint
- **Agent**: `backend-specialist`
- **Skill**: `api-patterns`
- **Priority**: P1
- **Dependencies**: Task 2
- **INPUT**: Service wrapper and RBAC deps
- **OUTPUT**: `app/api/copilot.py` and modified [app/api/routes.py](file:///c:/Users/anude/Documents/GitHub/enterprise-healthcare-rag/app/api/routes.py).
- **VERIFY**: `curl -X POST /api/v1/copilot/quick-help` with JWT token.

### Task 4: Integrate with Frontend State (`chatStore.ts`)
- **Agent**: `frontend-specialist`
- **Skill**: `clean-code`
- **Priority**: P2
- **Dependencies**: Task 3
- **INPUT**: New backend endpoint
- **OUTPUT**: Modified [frontend/src/store/chatStore.ts](file:///c:/Users/anude/Documents/GitHub/enterprise-healthcare-rag/frontend/src/store/chatStore.ts).
- **VERIFY**: FE logs show successful hits to the new endpoint.

## Phase X: Verification
1. **Security Scan**: `python .agent/skills/vulnerability-scanner/scripts/security_scan.py .`
2. **Linting**: `npm run lint` & Python `flake8`/`black` check in the backend.
3. **End-to-End Test**: Ensure the full pipeline runs via `uvicorn main:app --reload` and `npm run dev` without breaking the existing Stateful RAG Clarification Nodes.

## ✅ PHASE X COMPLETE
- Lint: [ ] Pending
- Security: [ ] Pending
- Build: [ ] Pending
- Date: [Pending]
