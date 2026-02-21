"""
API routes — Auth, ingestion, and query endpoints with RBAC enforcement.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request, Form
from typing import List, Optional
from app.schemas.models import (
    IngestResponse, QueryRequest, QueryResponse,
    LoginRequest, TokenResponse, UserCreate, UserOut,
    FeedbackRequest, FeedbackResponse,
)
from app.ingestion.loader_factory import LoaderFactory
from app.retrieval.vector_store import vector_store
from app.retrieval.graph import app_graph
from app.core.limiter import limiter
from app.core.config import settings
from app.security.auth import user_db, create_access_token, ROLE_HIERARCHY
from app.security.rbac import get_current_user, require_role, get_user_departments
from app.observability.tracing import build_langsmith_config, create_feedback as ls_create_feedback

router = APIRouter()
loader_factory = LoaderFactory()


# =========================================================================
# Auth endpoints
# =========================================================================

@router.post("/auth/login", response_model=TokenResponse)
async def login(request: Request, body: LoginRequest):
    """Authenticate and receive a JWT token."""
    user = user_db.authenticate(body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={
        "sub": user["username"],
        "role": user["role"],
        "departments": user["departments"],
    })

    return TokenResponse(
        access_token=token,
        user=UserOut(**{k: v for k, v in user.items() if k != "hashed_pw"}),
    )


@router.post("/auth/register", response_model=UserOut)
async def register_user(
    request: Request,
    body: UserCreate,
    admin: dict = Depends(require_role("admin")),
):
    """Admin-only: create a new user."""
    try:
        user = user_db.create_user(
            username=body.username,
            password=body.password,
            role=body.role,
            departments=body.departments,
            full_name=body.full_name,
        )
        return UserOut(**{k: v for k, v in user.items() if k != "hashed_pw"})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/auth/me", response_model=UserOut)
async def get_me(user: dict = Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    return UserOut(**{k: v for k, v in user.items() if k != "hashed_pw"})


@router.get("/admin/users", response_model=List[UserOut])
async def list_users(admin: dict = Depends(require_role("admin"))):
    """Admin-only: list all users."""
    return [
        UserOut(**{k: v for k, v in u.items() if k != "hashed_pw"})
        for u in user_db.list_users()
    ]


@router.delete("/admin/users/{username}")
async def delete_user(username: str, admin: dict = Depends(require_role("admin"))):
    """Admin-only: delete a user (cannot delete admins)."""
    if user_db.delete_user(username):
        return {"status": "deleted", "username": username}
    raise HTTPException(status_code=404, detail="User not found or is an admin")


# =========================================================================
# Department info
# =========================================================================

@router.get("/departments")
async def get_departments(user: dict = Depends(get_current_user)):
    """Return departments the current user can access."""
    depts = get_user_departments(user)
    return {
        "departments": depts,
        "all_departments": settings.departments_list,
        "role": user["role"],
    }


@router.get("/departments/stats")
async def get_department_stats(admin: dict = Depends(require_role("admin"))):
    """Admin-only: document counts per department."""
    return vector_store.get_collection_stats()


# =========================================================================
# Ingestion
# =========================================================================

@router.post("/ingest", response_model=IngestResponse)
@limiter.limit("10/minute")
async def ingest_document(
    request: Request,
    file: UploadFile = File(...),
    department: str = Form("general"),
    user: dict = Depends(get_current_user),
):
    """
    Upload a document to a specific department's knowledge base.
    Requires the user to have access to the target department.
    """
    department = department.lower()

    # Validate department access
    allowed = get_user_departments(user)
    if department not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"You do not have access to the '{department}' department",
        )

    if department not in settings.departments_list:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid department '{department}'. Valid: {settings.departments_list}",
        )

    try:
        content = await file.read()
        chunks = await loader_factory.process_file(content, file.filename, file.content_type)

        # Determine modality from the first chunk
        modality = chunks[0].modality if chunks else "text"

        # Route to department collection
        vector_store.add_chunks(chunks, department=department)

        return IngestResponse(
            file_id=file.filename,
            filename=file.filename,
            department=department,
            modality=modality,
            chunks_count=len(chunks),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error ingesting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# Query
# =========================================================================

@router.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute")
async def query_documents(
    request: Request,
    request_body: QueryRequest,
    user: dict = Depends(get_current_user),
):
    """
    Query the knowledge base. Searches only departments the user has access to.
    Optionally filter to specific departments via `request_body.departments`.
    """
    try:
        allowed = get_user_departments(user)

        # If user specified departments, intersect with allowed
        if request_body.departments:
            search_depts = [d for d in request_body.departments if d in allowed]
            if not search_depts:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have access to any of the requested departments",
                )
        else:
            search_depts = allowed

        # Build LangSmith config with hospital-specific metadata & tags
        langsmith_config = build_langsmith_config(
            user_id=user["username"],
            role=user["role"],
            departments=search_depts,
        )

        # Build graph input with RBAC context
        inputs = {
            "question": request_body.question,
            "role": user["role"],
            "departments": search_depts,
            "user_id": user["username"],
            "retry_count": 0,
            "hallucination_score": "",
            "query_transformations": [],
            "metadata": langsmith_config.get("metadata", {}),
            "clarification_needed": False,
            "clarification_options": [],
        }
        result = await app_graph.ainvoke(inputs, config=langsmith_config)

        answer = result.get(
            "generation",
            "No relevant documents found in the departments you have access to.",
        )
        docs = result.get("documents", [])
        hallucination_score = result.get("hallucination_score", "yes")

        # ── Clarification short-circuit ──────────────────────────────────────
        # If the clarification_check node flagged the query as ambiguous,
        # return the options immediately — no generation was performed.
        clarification_needed  = result.get("clarification_needed", False)
        clarification_options = result.get("clarification_options", [])

        if clarification_needed and clarification_options:
            return QueryResponse(
                answer="I'd like to make sure I give you the most relevant information. Could you clarify what you're looking for?",
                sources=[],
                departments_searched=search_depts,
                response_type="clarification",
                options=clarification_options,
            )

        # Confidence = average similarity score of top-3 retrieved sources
        top_scores = [d.score for d in docs[:3] if hasattr(d, "score") and d.score is not None]
        confidence_score = round(sum(top_scores) / max(len(top_scores), 1), 3) if top_scores else 0.0

        # De-anonymize for doctors
        if user["role"] == "doctor":
            from app.security.pii import pii_manager
            answer = pii_manager.deanonymize(answer)
            for doc in docs:
                doc.content = pii_manager.deanonymize(doc.content)

        return QueryResponse(
            answer=answer,
            sources=docs,
            departments_searched=search_depts,
            hallucination_score=hallucination_score,
            confidence_score=confidence_score,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# Feedback (LangSmith clinician corrections)
# =========================================================================

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: Request,
    body: FeedbackRequest,
    user: dict = Depends(get_current_user),
):
    """
    Submit clinician feedback for a previous query.

    When a doctor or nurse corrects the chatbot's response, this endpoint
    records the correction in LangSmith against the original trace so the
    team can measure and improve accuracy over time.
    """
    success = ls_create_feedback(
        run_id=body.run_id,
        key=body.key,
        score=body.score,
        comment=body.comment,
    )
    if not success:
        raise HTTPException(
            status_code=502,
            detail="Failed to record feedback — LangSmith may be unavailable",
        )
    return FeedbackResponse(
        status="recorded",
        run_id=body.run_id,
        key=body.key,
    )
