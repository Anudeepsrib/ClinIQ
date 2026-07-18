"""
API routes — Auth, ingestion, and query endpoints with RBAC enforcement.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, List
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)

from app.api.copilot import router as copilot_router
from app.chat.chat_history_store import chat_history_store
from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import redact_text
from app.ingestion.document_registry import document_registry
from app.ingestion.upsert_pipeline import delete_document as upsert_delete_document
from app.ingestion.upsert_pipeline import upsert_document
from app.observability.tracing import build_langsmith_config
from app.observability.tracing import create_feedback as ls_create_feedback
from app.retrieval.azure_search_store import azure_search_store
from app.retrieval.graph import app_graph
from app.schemas.chat_models import (
    ChatMessageOut,
    ChatSearchRequest,
    CreateSessionRequest,
    CreateSessionResponse,
    SessionSummaryOut,
)
from app.schemas.models import (
    DocumentHistory,
    DocumentInfo,
    FeedbackRequest,
    FeedbackResponse,
    IngestJobResponse,
    LoginRequest,
    QueryRequest,
    QueryResponse,
    TokenResponse,
    UpsertResponse,
    UserCreate,
    UserOut,
)
from app.security.auth import create_access_token, user_db
from app.security.pii import pii_manager
from app.security.rbac import get_current_user, get_user_departments, require_role
from app.security.uploads import read_limited_upload, sanitize_filename, validate_upload_metadata

router = APIRouter()
logger = logging.getLogger(__name__)

CurrentUser = Annotated[dict, Depends(get_current_user)]
AdminUser = Annotated[dict, Depends(require_role("admin"))]
UploadedDocument = Annotated[UploadFile, File()]
DepartmentForm = Annotated[str, Form()]

router.include_router(copilot_router)


@dataclass
class _IngestJob:
    owner: str
    response: IngestJobResponse


# ponytail: process-local jobs suit the single-worker reference app; use a durable queue for
# multi-worker or multi-replica deployments.
_ingest_jobs: dict[str, _IngestJob] = {}


def _validate_department_access(department: str, user: dict) -> str:
    department = department.lower()
    if department not in get_user_departments(user):
        raise HTTPException(
            status_code=403,
            detail=f"You do not have access to the '{department}' department",
        )
    if department not in settings.departments_list:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid department '{department}'. Valid: {settings.departments_list}",
        )
    return department


def _infer_modality(filename: str, content_type: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".dcm":
        return "dicom"
    if content_type.startswith("image/"):
        return "image"
    if content_type.startswith("audio/"):
        return "audio"
    if content_type.startswith("video/"):
        return "video"
    if suffix in {".xls", ".xlsx"}:
        return "table"
    return "document"


async def _run_ingest_job(
    job_id: str,
    content: bytes,
    filename: str,
    content_type: str,
    department: str,
    username: str,
) -> None:
    job = _ingest_jobs[job_id]
    job.response.status = "processing"
    try:
        result = await upsert_document(
            file_bytes=content,
            filename=filename,
            content_type=content_type,
            department=department,
            user=username,
        )
        job.response.result = UpsertResponse.model_validate(result, from_attributes=True)
        job.response.status = "completed"
    except Exception as exc:
        logger.exception("Background ingestion failed for %s: %s", filename, redact_text(exc))
        job.response.status = "failed"
        job.response.error = "Document ingestion failed"


# =========================================================================
# Auth endpoints
# =========================================================================

@router.post("/auth/login", response_model=TokenResponse)
@limiter.limit("5/minute")
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
@limiter.limit("10/minute")
async def register_user(
    request: Request,
    body: UserCreate,
    admin: AdminUser,
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
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/auth/me", response_model=UserOut)
async def get_me(user: CurrentUser):
    """Return the current authenticated user's profile."""
    return UserOut(**{k: v for k, v in user.items() if k != "hashed_pw"})


@router.get("/admin/users", response_model=List[UserOut])
async def list_users(admin: AdminUser):
    """Admin-only: list all users."""
    return [
        UserOut(**{k: v for k, v in u.items() if k != "hashed_pw"})
        for u in user_db.list_users()
    ]


@router.delete("/admin/users/{username}")
async def delete_user(username: str, admin: AdminUser):
    """Admin-only: delete a user (cannot delete admins)."""
    if user_db.delete_user(username):
        return {"status": "deleted", "username": username}
    raise HTTPException(status_code=404, detail="User not found or is an admin")


# =========================================================================
# Department info
# =========================================================================

@router.get("/departments")
async def get_departments(user: CurrentUser):
    """Return departments the current user can access."""
    depts = get_user_departments(user)
    return {
        "departments": depts,
        "all_departments": settings.departments_list,
        "role": user["role"],
    }


@router.get("/departments/stats")
async def get_department_stats(admin: AdminUser):
    """Admin-only: document counts per department."""
    return azure_search_store.get_collection_stats()


# =========================================================================
# Ingestion
# =========================================================================

@router.post("/ingest", response_model=UpsertResponse)
@limiter.limit("10/minute")
async def ingest_document(
    request: Request,
    file: UploadedDocument,
    user: CurrentUser,
    department: DepartmentForm = "general",
):
    """
    Upload a document to a specific department's knowledge base.
    Requires the user to have access to the target department.
    Routes through the intelligent upsert pipeline.
    """
    department = _validate_department_access(department, user)
    safe_filename = validate_upload_metadata(file)

    try:
        content = await read_limited_upload(file)
        username = user["username"]
        result = await upsert_document(
            file_bytes=content,
            filename=safe_filename,
            content_type=file.content_type,
            department=department,
            user=username
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error ingesting file %s: %s", safe_filename, redact_text(e))
        raise HTTPException(status_code=500, detail="Failed to ingest document") from e


@router.post("/ingest/jobs", response_model=IngestJobResponse, status_code=202)
@limiter.limit("10/minute")
async def create_ingest_job(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadedDocument,
    user: CurrentUser,
    department: DepartmentForm = "general",
):
    """Queue document ingestion and return a pollable status record."""
    department = _validate_department_access(department, user)
    safe_filename = validate_upload_metadata(file)
    content = await read_limited_upload(file)
    content_type = file.content_type or "application/octet-stream"
    job_id = str(uuid4())
    response = IngestJobResponse(
        job_id=job_id,
        filename=safe_filename,
        department=department,
        modality=_infer_modality(safe_filename, content_type),
    )
    _ingest_jobs[job_id] = _IngestJob(owner=user["username"], response=response)
    background_tasks.add_task(
        _run_ingest_job,
        job_id,
        content,
        safe_filename,
        content_type,
        department,
        user["username"],
    )
    return response


@router.get("/ingest/jobs/{job_id}", response_model=IngestJobResponse)
async def get_ingest_job(job_id: str, user: CurrentUser):
    """Return ingestion status to its owner or an administrator."""
    job = _ingest_jobs.get(job_id)
    if not job or (job.owner != user["username"] and user["role"] != "admin"):
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    return job.response


@router.get("/documents/{department}", response_model=List[DocumentInfo])
async def list_documents(department: str, user: CurrentUser):
    """List active documents in a department (RBAC enforced)."""
    department = department.lower()
    allowed = get_user_departments(user)
    if department not in allowed:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return document_registry.list_documents(department)


@router.delete("/documents/{department}/{filename}")
async def delete_document_ep(department: str, filename: str, admin: AdminUser):
    """Admin-only: soft-delete a document and purge vectors."""
    filename = sanitize_filename(filename)
    success = await upsert_delete_document(filename, department)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "filename": filename, "department": department}


@router.get("/documents/{department}/{filename}/history", response_model=DocumentHistory)
async def get_document_history(department: str, filename: str, user: CurrentUser):
    """Get full version history (RBAC enforced)."""
    department = department.lower()
    filename = sanitize_filename(filename)
    allowed = get_user_departments(user)
    if department not in allowed:
        raise HTTPException(status_code=403, detail="Unauthorized")
    doc_id = document_registry.build_doc_id(department, filename)
    history = document_registry.get_history(doc_id)
    return {"history": history}


# =========================================================================
# Query
# =========================================================================

@router.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute")
async def query_documents(
    request: Request,
    request_body: QueryRequest,
    user: CurrentUser,
):
    """
    Query the knowledge base. Searches only departments the user has access to.
    Optionally filter to specific departments via `request_body.departments`.
    """
    try:
        allowed = get_user_departments(user)

        # If user specified departments, intersect with allowed
        if request_body.departments:
            requested_departments = [d.lower() for d in request_body.departments]
            invalid_departments = [d for d in requested_departments if d not in settings.departments_list]
            if invalid_departments:
                raise HTTPException(status_code=400, detail="Invalid department requested")

            search_depts = [d for d in requested_departments if d in allowed]
            if not search_depts:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have access to any of the requested departments",
                )
        else:
            search_depts = allowed

        sanitized_question = pii_manager.anonymize(request_body.question)

        # Build LangSmith config with hospital-specific metadata & tags
        langsmith_config = build_langsmith_config(
            user_id=user["username"],
            role=user["role"],
            departments=search_depts,
        )
        trace_run_id = uuid4() if settings.ENABLE_EXTERNAL_TRACING else None
        if trace_run_id:
            langsmith_config["run_id"] = trace_run_id

        # Build graph input with RBAC context
        inputs = {
            "question": sanitized_question,
            "role": user["role"],
            "departments": search_depts,
            "user_id": user["username"],
            "llm_provider": request_body.provider or settings.LLM_PROVIDER,
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
                run_id=str(trace_run_id) if trace_run_id else None,
                feedback_enabled=bool(trace_run_id),
            )

        # Confidence = average similarity score of top-3 retrieved sources
        top_scores = [d.score for d in docs[:3] if hasattr(d, "score") and d.score is not None]
        confidence_score = round(sum(top_scores) / max(len(top_scores), 1), 3) if top_scores else 0.0

        # De-anonymize for doctors
        if user["role"] == "doctor":
            answer = pii_manager.deanonymize(answer)
            for doc in docs:
                doc.content = pii_manager.deanonymize(doc.content)

        # ── Append to Chat History if session_id provided ──
        if request_body.session_id:
            try:
                chat_history_store.append_message(
                    session_id=request_body.session_id,
                    user_id=user["username"],
                    role="user",
                    content=sanitized_question,
                    department=search_depts[0] if search_depts else "general"
                )
                chat_history_store.append_message(
                    session_id=request_body.session_id,
                    user_id=user["username"],
                    role="bot",
                    content=answer,
                    department=search_depts[0] if search_depts else "general"
                )
            except Exception as hist_err:
                logger.warning("Error appending chat history: %s", redact_text(hist_err))

        return QueryResponse(
            answer=answer,
            sources=docs,
            departments_searched=search_depts,
            hallucination_score=hallucination_score,
            confidence_score=confidence_score,
            run_id=str(trace_run_id) if trace_run_id else None,
            feedback_enabled=bool(trace_run_id),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing query: %s", redact_text(e))
        raise HTTPException(status_code=500, detail="Failed to process query") from e


# =========================================================================
# Feedback (LangSmith clinician corrections)
# =========================================================================

@router.post("/feedback", response_model=FeedbackResponse)
@limiter.limit("20/minute")
async def submit_feedback(
    request: Request,
    body: FeedbackRequest,
    user: CurrentUser,
):
    """
    Submit clinician feedback for a previous query.

    When a doctor or nurse corrects the chatbot's response, this endpoint
    records the correction in LangSmith against the original trace so the
    team can measure and improve accuracy over time.
    """
    success = ls_create_feedback(
        run_id=str(body.run_id),
        key=body.key,
        score=body.score,
        comment=pii_manager.anonymize(body.comment) if body.comment else None,
    )
    if not success:
        raise HTTPException(
            status_code=502,
            detail="Failed to record feedback — LangSmith may be unavailable",
        )
    return FeedbackResponse(
        status="recorded",
        run_id=str(body.run_id),
        key=body.key,
    )

# =========================================================================
# Chat History
# =========================================================================

def _require_chat_history() -> None:
    if not chat_history_store.enabled:
        raise HTTPException(status_code=503, detail="Chat history is disabled")


@router.post("/chat/sessions", response_model=CreateSessionResponse)
async def create_chat_session(req: CreateSessionRequest, user: CurrentUser):
    """Create a new chat session."""
    _require_chat_history()
    department = (req.department or "general").lower()
    allowed = get_user_departments(user)
    if department not in allowed:
        raise HTTPException(status_code=403, detail="Unauthorized department")
    session_id = chat_history_store.create_session(user["username"], department)
    return {"session_id": session_id, "status": "created"}


@router.get("/chat/sessions", response_model=List[SessionSummaryOut])
async def list_chat_sessions(user: CurrentUser):
    """List only the current user's sessions."""
    _require_chat_history()
    return [s.to_dict() for s in chat_history_store.list_sessions(user["username"])]


@router.get("/chat/sessions/{session_id}", response_model=List[ChatMessageOut])
async def get_chat_session(session_id: str, user: CurrentUser):
    """Get conversation only if owned by current user."""
    _require_chat_history()
    if user["role"] == "admin":
        messages = chat_history_store.admin_get_session(session_id)
    else:
        messages = chat_history_store.get_session(session_id, user["username"])
    return [m.to_dict() for m in messages]


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str, user: CurrentUser):
    """Delete session if owned by user or if admin (RBAC)."""
    _require_chat_history()
    if user["role"] == "admin":
        success = chat_history_store.admin_delete_session(session_id)
    else:
        success = chat_history_store.delete_session(session_id, user["username"])
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or forbidden")
    return {"status": "deleted", "session_id": session_id}


@router.post("/chat/search", response_model=List[ChatMessageOut])
async def search_chat_history(req: ChatSearchRequest, user: CurrentUser):
    """Semantic search scoped to current user's history only."""
    _require_chat_history()
    results = chat_history_store.search_history(user["username"], req.query, req.k)
    return [r.to_dict() for r in results]
