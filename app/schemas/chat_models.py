"""Chat-specific Pydantic models for API request/response serialization."""

from typing import List, Optional
from pydantic import BaseModel


class ChatMessageOut(BaseModel):
    role: str
    content: str
    session_id: str
    user_id: str
    department: str = ""
    timestamp: str = ""
    msg_index: int = 0


class SessionSummaryOut(BaseModel):
    session_id: str
    title: str
    created_at: str
    message_count: int
    department: str = ""


class CreateSessionRequest(BaseModel):
    department: str = ""


class CreateSessionResponse(BaseModel):
    session_id: str
    status: str = "created"


class ChatSearchRequest(BaseModel):
    query: str
    k: int = 10
