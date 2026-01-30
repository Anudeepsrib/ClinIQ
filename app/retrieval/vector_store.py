import chromadb
from chromadb.utils import embedding_functions
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from typing import List
from app.schemas.models import ProcessedChunk, RetrievalResult
from app.core.config import settings

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

    def search(self, query: str, k: int = 4) -> List[RetrievalResult]:
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

vector_store = VectorStore()
