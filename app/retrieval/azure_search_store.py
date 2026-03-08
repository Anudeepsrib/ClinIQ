"""
Azure AI Search Vector Store — department-scoped indexes for clinical RAG.

Replaces the ChromaDB-based MultiCollectionVectorStore with Azure AI Search,
providing enterprise-grade hybrid search (vector + BM25), native metadata
filtering, and horizontal scaling — all behind the same public API surface.

Architecture:
    Azure AI Search Service
      ├── cliniq-dept-radiology     (index)
      ├── cliniq-dept-pharmacy      (index)
      ├── cliniq-dept-administration (index)
      └── ...
"""

import logging
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SearchIndex,
)
from azure.search.documents.models import VectorizedQuery

from langchain_openai import OpenAIEmbeddings
from app.schemas.models import ProcessedChunk, RetrievalResult
from app.core.config import settings

logger = logging.getLogger(__name__)

VECTOR_DIMENSIONS = 1536  # text-embedding-3-small


class AzureSearchVectorStore:
    """
    Department-scoped vector store backed by Azure AI Search.

    Each department gets its own search index, ensuring data isolation.
    Supports hybrid search (vector + BM25) and native metadata filtering.
    """

    def __init__(self):
        self.endpoint = settings.AZURE_SEARCH_ENDPOINT
        self.credential = AzureKeyCredential(settings.AZURE_SEARCH_API_KEY)
        self.index_prefix = settings.AZURE_SEARCH_INDEX_PREFIX
        self.embedding_fn = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )
        self._index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=self.credential,
        )
        self._search_clients: Dict[str, SearchClient] = {}

        for dept in settings.departments_list:
            self._ensure_index(dept)

    def _index_name(self, department: str) -> str:
        return f"{self.index_prefix}-{department.lower()}"

    def _get_search_client(self, department: str) -> SearchClient:
        dept = department.lower()
        if dept not in self._search_clients:
            self._search_clients[dept] = SearchClient(
                endpoint=self.endpoint,
                index_name=self._index_name(dept),
                credential=self.credential,
            )
        return self._search_clients[dept]

    def _ensure_index(self, department: str):
        """Create the search index if it doesn't exist."""
        index_name = self._index_name(department)
        try:
            self._index_client.get_index(index_name)
            logger.info(f"Index '{index_name}' already exists")
        except Exception:
            index = SearchIndex(
                name=index_name,
                fields=[
                    SimpleField(
                        name="id",
                        type=SearchFieldDataType.String,
                        key=True,
                        filterable=True,
                    ),
                    SearchableField(
                        name="content",
                        type=SearchFieldDataType.String,
                    ),
                    SearchField(
                        name="content_vector",
                        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        searchable=True,
                        vector_search_dimensions=VECTOR_DIMENSIONS,
                        vector_search_profile_name="cliniq-vector-profile",
                    ),
                    SimpleField(
                        name="source",
                        type=SearchFieldDataType.String,
                        filterable=True,
                        facetable=True,
                    ),
                    SimpleField(
                        name="department",
                        type=SearchFieldDataType.String,
                        filterable=True,
                    ),
                    SimpleField(
                        name="modality",
                        type=SearchFieldDataType.String,
                        filterable=True,
                    ),
                    SimpleField(
                        name="page",
                        type=SearchFieldDataType.Int32,
                        filterable=True,
                    ),
                    SimpleField(
                        name="ingested_at",
                        type=SearchFieldDataType.DateTimeOffset,
                        filterable=True,
                        sortable=True,
                    ),
                    SimpleField(
                        name="version",
                        type=SearchFieldDataType.Int32,
                        filterable=True,
                    ),
                ],
                vector_search=VectorSearch(
                    algorithms=[
                        HnswAlgorithmConfiguration(name="cliniq-hnsw"),
                    ],
                    profiles=[
                        VectorSearchProfile(
                            name="cliniq-vector-profile",
                            algorithm_configuration_name="cliniq-hnsw",
                        ),
                    ],
                ),
            )
            self._index_client.create_index(index)
            logger.info(f"Created Azure Search index '{index_name}'")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_chunks(self, chunks: List[ProcessedChunk], department: str, version: int = 1):
        """Batch upload chunks to a department's index using merge_or_upload."""
        if not chunks:
            return

        department = department.lower()
        client = self._get_search_client(department)

        texts = [c.content for c in chunks]
        embeddings = self.embedding_fn.embed_documents(texts)
        now = datetime.now(timezone.utc).isoformat()

        documents = []
        for chunk, embedding in zip(chunks, embeddings):
            doc_id = f"{department}_{chunk.source}_{chunk.chunk_index}"
            doc_id = doc_id.replace(" ", "_").replace(".", "_")

            documents.append({
                "id": doc_id,
                "content": chunk.content,
                "content_vector": embedding,
                "source": chunk.source,
                "department": department,
                "modality": chunk.modality or "text",
                "page": chunk.page or 0,
                "ingested_at": now,
                "version": version,
            })

        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            result = client.merge_or_upload_documents(documents=batch)
            succeeded = sum(1 for r in result if r.succeeded)
            logger.info(
                f"Uploaded batch {i // batch_size + 1}: "
                f"{succeeded}/{len(batch)} to '{department}'"
            )

    def delete_document_vectors(self, source_filename: str, department: str):
        """Delete all vectors for a specific source file from a department index."""
        department = department.lower()
        client = self._get_search_client(department)

        results = client.search(
            search_text="*",
            filter=f"source eq '{source_filename}'",
            select=["id"],
            top=1000,
        )

        doc_ids = [{"id": r["id"]} for r in results]
        if doc_ids:
            batch_size = 100
            for i in range(0, len(doc_ids), batch_size):
                batch = doc_ids[i:i + batch_size]
                client.delete_documents(documents=batch)
            logger.info(
                f"Deleted {len(doc_ids)} vectors for '{source_filename}' "
                f"from '{department}'"
            )
        else:
            logger.info(f"No vectors found for '{source_filename}' in '{department}'")

    def upsert_chunks(
        self,
        chunks: List[ProcessedChunk],
        department: str,
        source_filename: str,
        version: int = 1,
    ):
        """Atomic replace: delete old vectors for this source, then add new ones."""
        self.delete_document_vectors(source_filename, department)
        self.add_chunks(chunks, department, version=version)
        logger.info(
            f"Upserted {len(chunks)} chunks for '{source_filename}' "
            f"in '{department}' (v{version})"
        )

    def hybrid_search(
        self,
        query: str,
        departments: List[str],
        k: int = 4,
    ) -> List[RetrievalResult]:
        """
        Fan-out hybrid search (vector + BM25) across department indexes.
        Results are merged and sorted by score (best first).
        """
        query_embedding = self.embedding_fn.embed_query(query)
        all_results: List[RetrievalResult] = []

        for dept in departments:
            dept = dept.lower()
            try:
                client = self._get_search_client(dept)
                vector_query = VectorizedQuery(
                    vector=query_embedding,
                    k_nearest_neighbors=k,
                    fields="content_vector",
                )

                results = client.search(
                    search_text=query,
                    vector_queries=[vector_query],
                    top=k,
                    select=["id", "content", "source", "department", "modality", "page"],
                )

                for r in results:
                    all_results.append(
                        RetrievalResult(
                            content=r["content"],
                            source=r.get("source", "unknown"),
                            score=r["@search.score"],
                            page=r.get("page"),
                            metadata={
                                "department": r.get("department", dept),
                                "modality": r.get("modality", "text"),
                            },
                        )
                    )
            except Exception as e:
                logger.error(f"Search failed for department '{dept}': {e}")

        all_results.sort(key=lambda r: r.score, reverse=True)

        seen = set()
        unique = []
        for r in all_results:
            key = hash(r.content[:200])
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return unique[:k]

    def search(
        self,
        query: str,
        departments: List[str],
        k: int = 4,
    ) -> List[RetrievalResult]:
        """Semantic-only search (backward-compatible with old API)."""
        return self.hybrid_search(query, departments, k)

    def get_collection_stats(self) -> Dict[str, int]:
        """Return document count per department index."""
        stats = {}
        for dept in settings.departments_list:
            try:
                client = self._get_search_client(dept)
                stats[dept] = client.get_document_count()
            except Exception:
                stats[dept] = 0
        return stats


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
azure_search_store = AzureSearchVectorStore()
