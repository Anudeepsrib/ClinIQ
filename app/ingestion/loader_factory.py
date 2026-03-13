from app.ingestion.parsers import DocumentParser
from app.ingestion.image_parser import parse_image, parse_dicom
from typing import List
from app.schemas.models import ProcessedChunk
from app.security.pii import pii_manager


# Audio/video MIME type mappings
AUDIO_MIME_TYPES = {
    ".mp3": "audio/mp3",
    ".wav": "audio/wav",
    ".m4a": "audio/m4a",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
}

VIDEO_MIME_TYPES = {
    ".mp4": "video/mp4",
    ".mov": "video/mov",
    ".avi": "video/avi",
    ".webm": "video/webm",
}


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
            # Attach raw PDF bytes to the first chunk for native Gemini PDF embedding
            if chunks:
                chunks[0].raw_bytes = file_content
                chunks[0].mime_type = "application/pdf"
                chunks[0].embedding_modality = "pdf"

        elif filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
            chunks = self.parser.parse_excel(file_content, filename)
        elif filename_lower.endswith(".docx"):
            chunks = await self.parser.parse_docx(file_content, filename)

        # --- Image parsers (multimodal) ---
        elif filename_lower.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
            chunks = parse_image(file_content, filename)
        elif filename_lower.endswith(".dcm"):
            chunks = parse_dicom(file_content, filename)

        # --- Audio files (native Gemini embedding) ---
        elif any(filename_lower.endswith(ext) for ext in AUDIO_MIME_TYPES):
            ext = "." + filename_lower.rsplit(".", 1)[-1]
            mime = AUDIO_MIME_TYPES[ext]
            chunks = [
                ProcessedChunk(
                    chunk_index=0,
                    content=f"[Audio file: {filename}] — Embedded natively via Gemini Embedding 2.",
                    source=filename,
                    modality="audio",
                    embedding_modality="audio",
                    raw_bytes=file_content,
                    mime_type=mime,
                    metadata={"type": "audio", "format": ext.lstrip(".")},
                )
            ]

        # --- Video files (native Gemini embedding) ---
        elif any(filename_lower.endswith(ext) for ext in VIDEO_MIME_TYPES):
            ext = "." + filename_lower.rsplit(".", 1)[-1]
            mime = VIDEO_MIME_TYPES[ext]
            chunks = [
                ProcessedChunk(
                    chunk_index=0,
                    content=f"[Video file: {filename}] — Embedded natively via Gemini Embedding 2.",
                    source=filename,
                    modality="video",
                    embedding_modality="video",
                    raw_bytes=file_content,
                    mime_type=mime,
                    metadata={"type": "video", "format": ext.lstrip(".")},
                )
            ]

        else:
            raise ValueError(
                f"Unsupported file type: {filename}. "
                "Accepted: PDF, DOCX, XLSX, PNG, JPG, TIFF, BMP, DCM, MP3, WAV, M4A, MP4, MOV"
            )

        # Post-process: PII anonymization on all text
        for chunk in chunks:
            chunk.content = pii_manager.anonymize(chunk.content)

        return chunks
