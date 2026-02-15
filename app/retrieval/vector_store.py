"""
Multi-collection vector store — one ChromaDB collection per hospital department.

Architecture:
    data/vector_db/
      ├── dept_radiology/      (isolated Chroma collection)
      ├── dept_pharmacy/
      ├── dept_administration/
      └── ...
"""

import chromadb
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.docstore.document import Document
from typing import List, Dict, Optional
from app.schemas.models import ProcessedChunk, RetrievalResult
from app.core.config import settings
import logging
import os

logger = logging.getLogger(__name__)


class MultiCollectionVectorStore:
    """
    Department-scoped vector store.

    Each department gets its own ChromaDB collection, ensuring complete data
    isolation between departments.  At query time, users can only search
    collections they have access to (enforced by `departments` parameter).
    """

    def __init__(self):
        self.base_dir = settings.CHROMA_PERSIST_DIRECTORY
        self.embedding_fn = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )
        # {department_name: Chroma instance}
        self._collections: Dict[str, Chroma] = {}
        # {department_name: BM25Retriever | None}
        self._bm25: Dict[str, Optional[BM25Retriever]] = {}

        # Eagerly initialise collections for all configured departments
        for dept in settings.departments_list:
            self._get_or_create_collection(dept)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _persist_dir(self, department: str) -> str:
        path = os.path.join(self.base_dir, f"dept_{department}")
        os.makedirs(path, exist_ok=True)
        return path

    def _get_or_create_collection(self, department: str) -> Chroma:
        if department in self._collections:
            return self._collections[department]

        collection = Chroma(
            persist_directory=self._persist_dir(department),
            embedding_function=self.embedding_fn,
            collection_name=f"dept_{department}",
        )
        self._collections[department] = collection
        self._init_bm25(department)
        return collection

    def _init_bm25(self, department: str):
        """Initialise BM25 retriever for a single department collection."""
        try:
            collection = self._collections[department]
            existing = collection.get()
            if existing and existing["documents"]:
                docs = [
                    Document(page_content=text, metadata=meta)
                    for text, meta in zip(existing["documents"], existing["metadatas"])
                ]
                self._bm25[department] = BM25Retriever.from_documents(docs)
                logger.info(f"BM25 init: {department} → {len(docs)} docs")
            else:
                self._bm25[department] = None
        except Exception as e:
            logger.error(f"BM25 init failed for {department}: {e}")
            self._bm25[department] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_chunks(self, chunks: List[ProcessedChunk], department: str):
        """Add chunks to a specific department's collection."""
        if not chunks:
            return

        department = department.lower()
        if department not in settings.departments_list:
            raise ValueError(f"Unknown department '{department}'. Valid: {settings.departments_list}")

        collection = self._get_or_create_collection(department)

        texts = [c.content for c in chunks]
        metadatas = []
        ids = []
        for c in chunks:
            meta = dict(c.metadata)
            meta["source"] = c.source
            meta["department"] = department
            meta["modality"] = c.modality or "text"
            if c.page:
                meta["page"] = c.page
            if c.sheet_name:
                meta["sheet_name"] = c.sheet_name
            metadatas.append(meta)
            ids.append(f"{department}_{c.source}_{c.chunk_index}")

        collection.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        self._init_bm25(department)  # Rebuild BM25 index
        logger.info(f"Added {len(chunks)} chunks to '{department}' collection")

    def hybrid_search(
        self, query: str, departments: List[str], k: int = 4
    ) -> List[RetrievalResult]:
        """
        Fan-out hybrid search across multiple department collections.
        Results are merged and sorted by score (best first).
        """
        all_results: List[RetrievalResult] = []

        for dept in departments:
            dept = dept.lower()
            collection = self._collections.get(dept)
            if not collection:
                continue

            chroma_retriever = collection.as_retriever(search_kwargs={"k": k})
            bm25 = self._bm25.get(dept)

            if bm25:
                bm25.k = k
                ensemble = EnsembleRetriever(
                    retrievers=[chroma_retriever, bm25],
                    weights=[0.5, 0.5],
                )
                docs = ensemble.invoke(query)
            else:
                docs = chroma_retriever.invoke(query)

            for doc in docs:
                all_results.append(
                    RetrievalResult(
                        content=doc.page_content,
                        source=doc.metadata.get("source", "unknown"),
                        score=0.0,
                        page=doc.metadata.get("page"),
                        metadata=doc.metadata,
                    )
                )

        # Deduplicate by content hash, keep first occurrence
        seen = set()
        unique = []
        for r in all_results:
            key = hash(r.content[:200])
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return unique[:k]

    def search(self, query: str, departments: List[str], k: int = 4) -> List[RetrievalResult]:
        """Simple semantic-only search across allowed departments."""
        all_results: List[RetrievalResult] = []

        for dept in departments:
            collection = self._collections.get(dept.lower())
            if not collection:
                continue
            docs = collection.similarity_search_with_score(query, k=k)
            for doc, score in docs:
                all_results.append(
                    RetrievalResult(
                        content=doc.page_content,
                        source=doc.metadata.get("source", "unknown"),
                        score=score,
                        page=doc.metadata.get("page"),
                        metadata=doc.metadata,
                    )
                )

        all_results.sort(key=lambda r: r.score)
        return all_results[:k]

    def get_collection_stats(self) -> Dict[str, int]:
        """Return document count per department (for admin dashboard)."""
        stats = {}
        for dept, coll in self._collections.items():
            try:
                data = coll.get()
                stats[dept] = len(data["documents"]) if data and data["documents"] else 0
            except Exception:
                stats[dept] = 0
        return stats


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
vector_store = MultiCollectionVectorStore()
