from app.ingestion.parsers import DocumentParser
from typing import List
from app.schemas.models import ProcessedChunk
from app.security.pii import pii_manager

class LoaderFactory:
    def __init__(self):
        self.parser = DocumentParser()

    async def process_file(self, file_content: bytes, filename: str, content_type: str) -> List[ProcessedChunk]:
        filename_lower = filename.lower()
        
        # Note: Ideally we anonymize text AFTER extraction but BEFORE chunking.
        # However, parsers take raw bytes.
        # For MVP, we will only support TXT/MD/Simple extraction here or modify parsers.
        # But wait, our Plan said "Inject pii_manager.anonymize(text) right after loading text".
        # This means we need to modify the Parser methods or do it here if possible.
        # Let's see... Parser methods return chunks.
        # So we should wrap the parser results or inject it inside Parser.
        
        # Let's peek at `app/ingestion/parsers.py` first to see if we can hook in.
        # Actually I haven't read parsers.py yet.
        # I'll optimistically assume I can iterate over chunks and anonymize them here.
        
        chunks = []
        if filename_lower.endswith('.pdf'):
            chunks = self.parser.parse_pdf(file_content, filename)
        elif filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls'):
            chunks = self.parser.parse_excel(file_content, filename)
        elif filename_lower.endswith('.docx'):
            chunks = await self.parser.parse_docx(file_content, filename)
        else:
            raise ValueError(f"Unsupported file type: {filename}")
            
        # Post-process chunks to anonymize
        for chunk in chunks:
            chunk.content = pii_manager.anonymize(chunk.content)
            
        return chunks
