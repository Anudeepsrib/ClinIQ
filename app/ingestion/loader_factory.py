from app.ingestion.parsers import DocumentParser
from typing import List
from app.schemas.models import ProcessedChunk

class LoaderFactory:
    def __init__(self):
        self.parser = DocumentParser()

    async def process_file(self, file_content: bytes, filename: str, content_type: str) -> List[ProcessedChunk]:
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.pdf'):
            return self.parser.parse_pdf(file_content, filename)
        elif filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls'):
            return self.parser.parse_excel(file_content, filename)
        elif filename_lower.endswith('.docx'):
            return await self.parser.parse_docx(file_content, filename)
        else:
            raise ValueError(f"Unsupported file type: {filename}")
