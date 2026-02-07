import chromadb
from chromadb.utils import embedding_functions
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.docstore.document import Document
from typing import List, Optional
from app.schemas.models import ProcessedChunk, RetrievalResult
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.persist_directory = settings.CHROMA_PERSIST_DIRECTORY
        self.embedding_fn = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY
        )
        self.vector_db = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_fn,
            collection_name="healthcare_docs"
        )
        self.bm25_retriever: Optional[BM25Retriever] = None
        self._initialize_bm25()

    def _initialize_bm25(self):
        """Initializes BM25 retriever from existing Chroma documents."""
        try:
            # Fetch all documents from Chroma
            existing_data = self.vector_db.get()
            if existing_data and existing_data['documents']:
                docs = [
                    Document(page_content=text, metadata=meta) 
                    for text, meta in zip(existing_data['documents'], existing_data['metadatas'])
                ]
                self.bm25_retriever = BM25Retriever.from_documents(docs)
                logger.info(f"Initialized BM25 with {len(docs)} documents.")
            else:
                logger.info("ChromaDB is empty. BM25 not initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize BM25: {e}")

    def add_chunks(self, chunks: List[ProcessedChunk]):
        if not chunks:
            return
            
        texts = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        ids = [f"{chunk.source}_{chunk.chunk_index}" for chunk in chunks]
        
        # Add source file to metadata for filtering
        for i, chunk in enumerate(chunks):
            metadatas[i]["source"] = chunk.source
            if chunk.page:
                metadatas[i]["page"] = chunk.page
            if chunk.sheet_name:
                metadatas[i]["sheet_name"] = chunk.sheet_name
        
        self.vector_db.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        
        # Re-initialize BM25 after adding new chunks
        # Note: For production, this should be optimized to incremental updates if possible
        self._initialize_bm25()

    def search(self, query: str, k: int = 4) -> List[RetrievalResult]:
        """Legacy semantic search."""
        docs = self.vector_db.similarity_search_with_score(query, k=k)
        results = []
        for doc, score in docs:
            results.append(RetrievalResult(
                content=doc.page_content,
                source=doc.metadata.get("source", "unknown"),
                score=score,
                page=doc.metadata.get("page"),
                metadata=doc.metadata
            ))
        return results

    def hybrid_search(self, query: str, k: int = 4) -> List[RetrievalResult]:
        """Performs hybrid search using EnsembleRetriever (Semantic + BM25)."""
        chroma_retriever = self.vector_db.as_retriever(search_kwargs={"k": k})
        
        if self.bm25_retriever:
            self.bm25_retriever.k = k
            ensemble_retriever = EnsembleRetriever(
                retrievers=[chroma_retriever, self.bm25_retriever],
                weights=[0.5, 0.5]
            )
            docs = ensemble_retriever.invoke(query)
        else:
            # Fallback to semantic search if BM25 is not ready
            docs = chroma_retriever.invoke(query)

        # Convert to RetrievalResult
        results = []
        for doc in docs:
            # EnsembleRetriever doesn't return scores by default in the same way, 
            # so we might miss the 'score' field or would need to recalculate.
            # For MVP, we'll omit the score or set a placeholder.
            results.append(RetrievalResult(
                content=doc.page_content,
                source=doc.metadata.get("source", "unknown"),
                score=0.0, # Placeholder as Ensemble doesn't provide unified score easily
                page=doc.metadata.get("page"),
                metadata=doc.metadata
            ))
        return results

vector_store = VectorStore()
