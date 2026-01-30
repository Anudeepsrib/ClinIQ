from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class IngestRequest(BaseModel):
    filename: str
    content_type: str

class IngestResponse(BaseModel):
    file_id: str
    filename: str
    status: str = "processed"
    chunks_count: int

class ProcessedChunk(BaseModel):
    chunk_index: int
    content: str
    source: str
    page: Optional[int] = None
    sheet_name: Optional[str] = None
    row_range: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RetrievalResult(BaseModel):
    content: str
    source: str
    score: float
    page: Optional[int] = None
    metadata: Dict[str, Any] = {}

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[RetrievalResult]
