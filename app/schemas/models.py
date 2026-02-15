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


class ProcessedChunk(BaseModel):
    chunk_index: int
    content: str
    source: str
    page: Optional[int] = None
    sheet_name: Optional[str] = None
    row_range: Optional[str] = None
    modality: Optional[str] = "text"  # text | image | table | dicom
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


class QueryResponse(BaseModel):
    answer: str
    sources: List[RetrievalResult]
    departments_searched: List[str] = []
