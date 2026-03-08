"""
Document Registry — SQLite-backed version tracker for ingested documents.

Tracks every file ingested into the vector store with content hashing (SHA-256)
for change detection. Enables the upsert pipeline to skip unchanged documents,
replace stale vectors, and maintain a full audit trail of document versions.

Schema:
    doc_id       TEXT    {department}_{filename}
    filename     TEXT    Original filename
    department   TEXT    Target department
    content_hash TEXT    SHA-256 of raw file bytes
    chunk_count  INT     Number of vectors produced
    version      INT     Auto-incrementing per doc_id
    ingested_by  TEXT    Username who uploaded
    ingested_at  TEXT    ISO timestamp
    status       TEXT    active | superseded | deleted
"""

import sqlite3
import hashlib
import os
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

DB_PATH = os.path.join("data", "document_registry.db")


class DocumentRegistry:
    """Lightweight SQLite registry for tracking ingested document versions."""

    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id      TEXT NOT NULL,
                    filename    TEXT NOT NULL,
                    department  TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    version     INTEGER NOT NULL DEFAULT 1,
                    ingested_by TEXT NOT NULL,
                    ingested_at TEXT NOT NULL,
                    status      TEXT NOT NULL DEFAULT 'active'
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_doc_id_status
                ON documents(doc_id, status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_department_status
                ON documents(department, status)
            """)
            conn.commit()

    @staticmethod
    def compute_hash(file_bytes: bytes) -> str:
        """SHA-256 hash of raw file content."""
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def build_doc_id(department: str, filename: str) -> str:
        return f"{department.lower()}_{filename}"

    def lookup(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Return the latest active record for a doc_id, or None."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE doc_id = ? AND status = 'active' "
                "ORDER BY version DESC LIMIT 1",
                (doc_id,),
            ).fetchone()
            return dict(row) if row else None

    def has_changed(self, doc_id: str, new_hash: str) -> bool:
        """True if the document is new or its content hash differs."""
        existing = self.lookup(doc_id)
        if not existing:
            return True
        return existing["content_hash"] != new_hash

    def register(
        self,
        doc_id: str,
        filename: str,
        department: str,
        content_hash: str,
        chunk_count: int,
        ingested_by: str,
    ) -> Dict[str, Any]:
        """Insert a new active version. Returns the new record."""
        existing = self.lookup(doc_id)
        version = (existing["version"] + 1) if existing else 1

        now = datetime.now(timezone.utc).isoformat()

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO documents
                    (doc_id, filename, department, content_hash, chunk_count,
                     version, ingested_by, ingested_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
                """,
                (doc_id, filename, department, content_hash,
                 chunk_count, version, ingested_by, now),
            )
            conn.commit()

        logger.info(f"Registered {doc_id} v{version} ({chunk_count} chunks)")
        return {
            "doc_id": doc_id,
            "filename": filename,
            "department": department,
            "content_hash": content_hash,
            "chunk_count": chunk_count,
            "version": version,
            "ingested_by": ingested_by,
            "ingested_at": now,
            "status": "active",
        }

    def mark_superseded(self, doc_id: str):
        """Mark all active versions of a doc_id as superseded."""
        with self._conn() as conn:
            conn.execute(
                "UPDATE documents SET status = 'superseded' "
                "WHERE doc_id = ? AND status = 'active'",
                (doc_id,),
            )
            conn.commit()
        logger.info(f"Superseded all active versions of {doc_id}")

    def mark_deleted(self, doc_id: str):
        """Soft-delete: mark all versions as deleted."""
        with self._conn() as conn:
            conn.execute(
                "UPDATE documents SET status = 'deleted' "
                "WHERE doc_id = ? AND status IN ('active', 'superseded')",
                (doc_id,),
            )
            conn.commit()
        logger.info(f"Soft-deleted {doc_id}")

    def list_documents(self, department: str) -> List[Dict[str, Any]]:
        """Return all active documents for a department."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM documents WHERE department = ? AND status = 'active' "
                "ORDER BY ingested_at DESC",
                (department.lower(),),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_history(self, doc_id: str) -> List[Dict[str, Any]]:
        """Full version history for audit trail."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM documents WHERE doc_id = ? ORDER BY version DESC",
                (doc_id,),
            ).fetchall()
            return [dict(r) for r in rows]


# Singleton
document_registry = DocumentRegistry()
