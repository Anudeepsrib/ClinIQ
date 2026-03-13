from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Auth / User schemas
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str = ""
    role: str = "viewer"
    departments: Optional[List[str]] = None


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    departments: List[str]
    is_active: bool
    created_at: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------------------------------------------------------------------------
# Ingestion schemas
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    filename: str
    content_type: str


class IngestResponse(BaseModel):
    file_id: str
    filename: str
    department: str = "general"
    modality: str = "text"
    status: str = "processed"
    chunks_count: int


class UpsertResponse(BaseModel):
    doc_id: str
    filename: str
    department: str
    change_type: str        # 'new', 'updated', 'unchanged'
    version: int
    chunk_count: int
    content_hash: str
    previous_version: Optional[int] = None


class DocumentInfo(BaseModel):
    doc_id: str
    filename: str
    department: str
    content_hash: str
    chunk_count: int
    version: int
    ingested_by: str
    ingested_at: str
    status: str


class DocumentHistory(BaseModel):
    history: List[DocumentInfo]


class ProcessedChunk(BaseModel):
    chunk_index: int
    content: str
    source: str
    page: Optional[int] = None
    sheet_name: Optional[str] = None
    row_range: Optional[str] = None
    modality: Optional[str] = "text"  # text | image | table | dicom
    embedding_modality: str = "text"  # text | image | pdf | audio | video (for Gemini)
    raw_bytes: Optional[bytes] = None  # raw binary data for native multimodal embedding
    mime_type: Optional[str] = None    # MIME type for raw_bytes (e.g. image/png)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Query schemas
# ---------------------------------------------------------------------------

class RetrievalResult(BaseModel):
    content: str
    source: str
    score: float
    page: Optional[int] = None
    metadata: Dict[str, Any] = {}


class QueryRequest(BaseModel):
    question: str
    departments: Optional[List[str]] = None  # filter to specific departments
    session_id: Optional[str] = None         # enable chat history appending


class QueryResponse(BaseModel):
    answer: str
    sources: List[RetrievalResult]
    departments_searched: List[str] = []
    hallucination_score: str = "yes"   # "yes" = grounded, "no" = hallucinated
    confidence_score: float = 0.0      # 0.0–1.0, average similarity of top sources
    response_type: str = "answer"      # "answer" | "clarification"
    options: List[str] = []            # clarification options (when response_type == "clarification")


# ---------------------------------------------------------------------------
# Feedback schemas (LangSmith clinician corrections)
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    run_id: str
    key: str = "correctness"  # e.g. "correctness", "relevance", "safety"
    score: float = Field(ge=0.0, le=1.0)
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    status: str
    run_id: str
    key: str
