"""
Chat History Store — ChromaDB-in-Azure for persistent conversation memory.

Stores and retrieves chat sessions with full RBAC isolation:
    - Each message is embedded and stored with user_id + session_id metadata
    - Users can ONLY access their own sessions (enforced at the store level)
    - Admins can access any session for compliance auditing
    - Semantic search across past conversations ("What did I ask about heparin?")

Backed by a ChromaDB instance hosted in Azure (Container App / VM).
"""

import chromadb
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from langchain_openai import OpenAIEmbeddings
from app.core.config import settings

logger = logging.getLogger(__name__)


class ChatMessage:
    """A single chat message."""

    def __init__(
        self,
        role: str,
        content: str,
        session_id: str,
        user_id: str,
        department: str = "",
        timestamp: str = "",
        msg_index: int = 0,
    ):
        self.role = role
        self.content = content
        self.session_id = session_id
        self.user_id = user_id
        self.department = department
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.msg_index = msg_index

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "department": self.department,
            "timestamp": self.timestamp,
            "msg_index": self.msg_index,
        }


class SessionSummary:
    """Lightweight session metadata for the sidebar."""

    def __init__(
        self,
        session_id: str,
        title: str,
        created_at: str,
        message_count: int,
        department: str = "",
    ):
        self.session_id = session_id
        self.title = title
        self.created_at = created_at
        self.message_count = message_count
        self.department = department

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "title": self.title,
            "created_at": self.created_at,
            "message_count": self.message_count,
            "department": self.department,
        }


class ChatHistoryStore:
    """
    ChromaDB-backed chat history with RBAC-enforced user isolation.

    Every method that reads data requires a user_id parameter and filters
    results to only that user's data. Admin override is handled at the
    API layer, not here — the store is strict about isolation.
    """

    COLLECTION_NAME = "cliniq_chat_history"

    def __init__(self):
        host = getattr(settings, "AZURE_CHROMA_HOST", "localhost")
        port = getattr(settings, "AZURE_CHROMA_PORT", 8000)
        auth_token = getattr(settings, "AZURE_CHROMA_AUTH_TOKEN", "")

        if host == "localhost":
            self._client = chromadb.Client()
            logger.info("ChatHistoryStore: using in-memory ChromaDB")
        else:
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            self._client = chromadb.HttpClient(
                host=host,
                port=port,
                headers=headers,
            )
            logger.info(f"ChatHistoryStore: connecting to {host}:{port}")

        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        self.embedding_fn = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )

    def create_session(self, user_id: str, department: str = "") -> str:
        """Create a new chat session. Returns session_id."""
        session_id = str(uuid.uuid4())
        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id

    def append_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        department: str = "",
    ) -> ChatMessage:
        """Embed and store a single chat turn."""
        existing = self._collection.get(
            where={"session_id": session_id},
        )
        msg_index = len(existing["ids"]) if existing["ids"] else 0
        doc_id = f"{session_id}_{msg_index}"
        now = datetime.now(timezone.utc).isoformat()

        embedding = self.embedding_fn.embed_query(content)

        self._collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[{
                "role": role,
                "session_id": session_id,
                "user_id": user_id,
                "department": department,
                "timestamp": now,
                "msg_index": msg_index,
            }],
        )

        logger.info(f"Appended msg {msg_index} to session {session_id}")
        return ChatMessage(
            role=role,
            content=content,
            session_id=session_id,
            user_id=user_id,
            department=department,
            timestamp=now,
            msg_index=msg_index,
        )

    def get_session(
        self, session_id: str, user_id: str
    ) -> List[ChatMessage]:
        """
        Retrieve all messages in a session, ordered by msg_index.
        Returns empty list if user_id doesn't own this session.
        """
        results = self._collection.get(
            where={
                "$and": [
                    {"session_id": session_id},
                    {"user_id": user_id},
                ]
            },
            include=["documents", "metadatas"],
        )

        if not results["ids"]:
            return []

        messages = []
        for doc, meta in zip(results["documents"], results["metadatas"]):
            messages.append(ChatMessage(
                role=meta["role"],
                content=doc,
                session_id=meta["session_id"],
                user_id=meta["user_id"],
                department=meta.get("department", ""),
                timestamp=meta.get("timestamp", ""),
                msg_index=meta.get("msg_index", 0),
            ))

        messages.sort(key=lambda m: m.msg_index)
        return messages

    def search_history(
        self, user_id: str, query: str, k: int = 10
    ) -> List[ChatMessage]:
        """Semantic search across a user's past conversations."""
        query_embedding = self.embedding_fn.embed_query(query)

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where={"user_id": user_id},
            include=["documents", "metadatas", "distances"],
        )

        if not results["ids"] or not results["ids"][0]:
            return []

        messages = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            messages.append(ChatMessage(
                role=meta["role"],
                content=doc,
                session_id=meta["session_id"],
                user_id=meta["user_id"],
                department=meta.get("department", ""),
                timestamp=meta.get("timestamp", ""),
                msg_index=meta.get("msg_index", 0),
            ))

        return messages

    def list_sessions(self, user_id: str) -> List[SessionSummary]:
        """Return all sessions for a user (for the sidebar)."""
        results = self._collection.get(
            where={"user_id": user_id},
            include=["documents", "metadatas"],
        )

        if not results["ids"]:
            return []

        sessions: Dict[str, Dict[str, Any]] = {}
        for doc, meta in zip(results["documents"], results["metadatas"]):
            sid = meta["session_id"]
            if sid not in sessions:
                sessions[sid] = {
                    "session_id": sid,
                    "first_message": doc[:80],
                    "created_at": meta.get("timestamp", ""),
                    "department": meta.get("department", ""),
                    "count": 0,
                }
            sessions[sid]["count"] += 1

        return [
            SessionSummary(
                session_id=s["session_id"],
                title=s["first_message"],
                created_at=s["created_at"],
                message_count=s["count"],
                department=s["department"],
            )
            for s in sorted(
                sessions.values(), key=lambda x: x["created_at"], reverse=True
            )
        ]

    def delete_session(self, session_id: str, user_id: str) -> bool:
        """
        Delete a session. Only succeeds if the user owns the session.
        Admin bypass is handled at the API layer.
        """
        results = self._collection.get(
            where={
                "$and": [
                    {"session_id": session_id},
                    {"user_id": user_id},
                ]
            },
        )

        if not results["ids"]:
            return False

        self._collection.delete(ids=results["ids"])
        logger.info(f"Deleted session {session_id} ({len(results['ids'])} messages)")
        return True

    def admin_get_session(self, session_id: str) -> List[ChatMessage]:
        """Admin-only: retrieve any session regardless of owner."""
        results = self._collection.get(
            where={"session_id": session_id},
            include=["documents", "metadatas"],
        )

        if not results["ids"]:
            return []

        messages = []
        for doc, meta in zip(results["documents"], results["metadatas"]):
            messages.append(ChatMessage(
                role=meta["role"],
                content=doc,
                session_id=meta["session_id"],
                user_id=meta["user_id"],
                department=meta.get("department", ""),
                timestamp=meta.get("timestamp", ""),
                msg_index=meta.get("msg_index", 0),
            ))

        messages.sort(key=lambda m: m.msg_index)
        return messages

    def admin_delete_session(self, session_id: str) -> bool:
        """Admin-only: delete any session."""
        results = self._collection.get(
            where={"session_id": session_id},
        )
        if not results["ids"]:
            return False
        self._collection.delete(ids=results["ids"])
        logger.info(f"Admin deleted session {session_id}")
        return True


# Singleton
chat_history_store = ChatHistoryStore()
