from app.ingestion.parsers import DocumentParser
from app.ingestion.image_parser import parse_image, parse_dicom
from typing import List
from app.schemas.models import ProcessedChunk
from app.security.pii import pii_manager


class LoaderFactory:
    def __init__(self):
        self.parser = DocumentParser()

    async def process_file(
        self, file_content: bytes, filename: str, content_type: str
    ) -> List[ProcessedChunk]:
        filename_lower = filename.lower()

        chunks = []

        # --- Text document parsers ---
        if filename_lower.endswith(".pdf"):
            chunks = self.parser.parse_pdf(file_content, filename)
        elif filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
            chunks = self.parser.parse_excel(file_content, filename)
        elif filename_lower.endswith(".docx"):
            chunks = await self.parser.parse_docx(file_content, filename)

        # --- Image parsers (multimodal) ---
        elif filename_lower.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
            chunks = parse_image(file_content, filename)
        elif filename_lower.endswith(".dcm"):
            chunks = parse_dicom(file_content, filename)

        else:
            raise ValueError(
                f"Unsupported file type: {filename}. "
                "Accepted: PDF, DOCX, XLSX, PNG, JPG, TIFF, BMP, DCM"
            )

        # Post-process: PII anonymization on all text
        for chunk in chunks:
            chunk.content = pii_manager.anonymize(chunk.content)

        return chunks
