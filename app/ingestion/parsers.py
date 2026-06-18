import io
from typing import List

import pandas as pd
from pypdf import PdfReader

from app.ingestion.chunker import ContentChunker
from app.schemas.models import ProcessedChunk


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
            for content in text_chunks:
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
            
            for content in str_chunks:
                chunks.append(ProcessedChunk(
                    chunk_index=len(chunks),
                    content=content,
                    source=filename,
                    sheet_name=sheet_name,
                    metadata={"type": "excel"}
                ))
        return chunks

    async def parse_docx(self, file_content: bytes, filename: str) -> List[ProcessedChunk]:
        """Extract DOCX text with unstructured and chunk it."""
        from unstructured.partition.docx import partition_docx

        elements = partition_docx(file=io.BytesIO(file_content))
        text = "\n\n".join([str(el) for el in elements])
        
        text_chunks = self.chunker.chunk_text(text)
        chunks = []
        for content in text_chunks:
            chunks.append(ProcessedChunk(
                chunk_index=len(chunks),
                content=content,
                source=filename,
                metadata={"type": "docx"}
            ))
        return chunks
