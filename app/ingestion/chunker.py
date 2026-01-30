from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter

class ContentChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk_text(self, text: str) -> List[str]:
        """Semantically chunks text content."""
        if not text:
            return []
        return self.text_splitter.split_text(text)

    def chunk_excel(self, rows: List[Dict[str, Any]], header_rows: int = 1) -> List[str]:
        """
        Chunks Excel content by converting rows to string representation.
        Preserves headers using 'Key: Value' format for every row to maintain context.
        Groups multiple rows into a single chunk if they are small.
        """
        chunks = []
        current_chunk = []
        current_length = 0
        
        for row in rows:
            # Convert row to string representation "Col1: Val1, Col2: Val2..."
            row_str = " | ".join([f"{k}: {v}" for k, v in row.items() if v is not None])
            row_len = len(row_str)
            
            if current_length + row_len > self.chunk_size and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_length = 0
            
            current_chunk.append(row_str)
            current_length += row_len
            
        if current_chunk:
            chunks.append("\n".join(current_chunk))
            
        return chunks
