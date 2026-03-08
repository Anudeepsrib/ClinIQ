"""
Upsert Pipeline — intelligent document ingestion with change detection.

Orchestrates the full flow:
    1. Hash incoming file (SHA-256)
    2. Check document registry for changes
    3. Parse & chunk via LoaderFactory (with PII anonymization)
    4. Upsert vectors in Azure AI Search (delete stale → add fresh)
    5. Update registry with new version

Unchanged documents are skipped entirely — zero wasted compute.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from app.ingestion.document_registry import document_registry, DocumentRegistry
from app.ingestion.loader_factory import LoaderFactory
from app.retrieval.azure_search_store import azure_search_store

logger = logging.getLogger(__name__)

loader_factory = LoaderFactory()


@dataclass
class UpsertResult:
    """Result of an upsert operation."""
    doc_id: str
    filename: str
    department: str
    change_type: str        # "new" | "updated" | "unchanged"
    version: int
    chunk_count: int
    content_hash: str
    previous_version: Optional[int] = None


async def upsert_document(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    department: str,
    user: str,
) -> UpsertResult:
    """
    Intelligently ingest a document — skip if unchanged, replace if modified.

    Args:
        file_bytes:   Raw file content
        filename:     Original filename
        content_type: MIME type
        department:   Target department (lowercase)
        user:         Username of the uploader

    Returns:
        UpsertResult with change_type, version, and chunk count.
    """
    department = department.lower()

    # 1. Compute content hash
    content_hash = DocumentRegistry.compute_hash(file_bytes)
    doc_id = DocumentRegistry.build_doc_id(department, filename)

    # 2. Check for changes
    if not document_registry.has_changed(doc_id, content_hash):
        existing = document_registry.lookup(doc_id)
        logger.info(f"Document unchanged: {doc_id} (v{existing['version']})")
        return UpsertResult(
            doc_id=doc_id,
            filename=filename,
            department=department,
            change_type="unchanged",
            version=existing["version"],
            chunk_count=existing["chunk_count"],
            content_hash=content_hash,
        )

    # 3. Determine if this is new or an update
    existing = document_registry.lookup(doc_id)
    is_update = existing is not None
    previous_version = existing["version"] if is_update else None

    # 4. Parse file through the loader factory (PII anonymization included)
    chunks = await loader_factory.process_file(file_bytes, filename, content_type)

    if not chunks:
        logger.warning(f"No chunks produced for {filename}")
        return UpsertResult(
            doc_id=doc_id,
            filename=filename,
            department=department,
            change_type="new" if not is_update else "updated",
            version=(previous_version + 1) if previous_version else 1,
            chunk_count=0,
            content_hash=content_hash,
            previous_version=previous_version,
        )

    # 5. Mark old version as superseded (if updating)
    if is_update:
        document_registry.mark_superseded(doc_id)
        logger.info(f"Superseding {doc_id} v{previous_version}")

    # 6. Upsert vectors in Azure AI Search
    new_version = (previous_version + 1) if previous_version else 1
    azure_search_store.upsert_chunks(
        chunks=chunks,
        department=department,
        source_filename=filename,
        version=new_version,
    )

    # 7. Register the new version
    document_registry.register(
        doc_id=doc_id,
        filename=filename,
        department=department,
        content_hash=content_hash,
        chunk_count=len(chunks),
        ingested_by=user,
    )

    change_type = "updated" if is_update else "new"
    logger.info(
        f"Upsert complete: {doc_id} → {change_type} "
        f"(v{new_version}, {len(chunks)} chunks)"
    )

    return UpsertResult(
        doc_id=doc_id,
        filename=filename,
        department=department,
        change_type=change_type,
        version=new_version,
        chunk_count=len(chunks),
        content_hash=content_hash,
        previous_version=previous_version,
    )


async def delete_document(
    filename: str,
    department: str,
) -> bool:
    """
    Soft-delete a document: remove vectors from Azure AI Search
    and mark the registry entry as deleted.
    """
    department = department.lower()
    doc_id = DocumentRegistry.build_doc_id(department, filename)

    existing = document_registry.lookup(doc_id)
    if not existing:
        return False

    azure_search_store.delete_document_vectors(filename, department)
    document_registry.mark_deleted(doc_id)
    logger.info(f"Deleted document: {doc_id}")
    return True
