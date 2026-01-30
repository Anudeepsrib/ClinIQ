import io
import pandas as pd
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader
from app.schemas.models import ProcessedChunk
from app.ingestion.chunker import ContentChunker

class DocumentParser:
    def __init__(self):
        self.chunker = ContentChunker()

    def parse_pdf(self, file_content: bytes, filename: str) -> List[ProcessedChunk]:
        """Extracts text from PDF and chunks it."""
        reader = PdfReader(io.BytesIO(file_content))
        chunks = []
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text:
                continue
            
            # Chunk the page content
            text_chunks = self.chunker.chunk_text(text)
            for idx, content in enumerate(text_chunks):
                chunks.append(ProcessedChunk(
                    chunk_index=len(chunks),
                    content=content,
                    source=filename,
                    page=i + 1,
                    metadata={"type": "pdf"}
                ))
        return chunks

    def parse_excel(self, file_content: bytes, filename: str) -> List[ProcessedChunk]:
        """Extracts rows from Excel, chunks them while preserving headers."""
        chunks = []
        excel_file = pd.ExcelFile(io.BytesIO(file_content))
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            # Replace NaN with None or empty string for cleaner output
            df = df.where(pd.notnull(df), None)
            
            # Convert to list of dicts
            rows = df.to_dict(orient='records')
            
            # Generate string chunks
            str_chunks = self.chunker.chunk_excel(rows)
            
            for idx, content in enumerate(str_chunks):
                chunks.append(ProcessedChunk(
                    chunk_index=len(chunks),
                    content=content,
                    source=filename,
                    sheet_name=sheet_name,
                    metadata={"type": "excel"}
                ))
        return chunks

    async def parse_docx(self, file_content: bytes, filename: str) -> List[ProcessedChunk]:
        """
        Parses DOCX using python-docx (lightweight) or unstructured.
        For MVP, we can simulate or use a simple xml parser if unstructured is strict dep.
        Let's use a simple approach for now or assume unstructured is installed.
        For now, I will use a placeholder or basic text extraction if unstructured is heavy.
        Actually, let's use unstructured since it was in requirements.
        """
        from unstructured.partition.docx import partition_docx
        
        # Save to temp file because unstructured likes paths or file-like objects
        # efficient file-like object handling
        elements = partition_docx(file=io.BytesIO(file_content))
        text = "\n\n".join([str(el) for el in elements])
        
        text_chunks = self.chunker.chunk_text(text)
        chunks = []
        for idx, content in enumerate(text_chunks):
            chunks.append(ProcessedChunk(
                chunk_index=len(chunks),
                content=content,
                source=filename,
                metadata={"type": "docx"}
            ))
        return chunks
