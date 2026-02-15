"""
Image and DICOM parsers for multimodal ingestion.

- Images (PNG, JPEG, TIFF, BMP): OCR text extraction via Tesseract
- DICOM (.dcm): Metadata text extraction (study description, modality, body part)
"""

import io
import logging
from typing import List

from app.schemas.models import ProcessedChunk
from app.ingestion.chunker import ContentChunker

logger = logging.getLogger(__name__)
chunker = ContentChunker()


def parse_image(file_content: bytes, filename: str) -> List[ProcessedChunk]:
    """
    Extract text from an image using OCR (Tesseract).
    Falls back gracefully if Tesseract is not installed.
    """
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        logger.error("Pillow or pytesseract not installed. Run: pip install Pillow pytesseract")
        return [
            ProcessedChunk(
                chunk_index=0,
                content=f"[Image file: {filename}] — OCR libraries not available. "
                        "Install Pillow and pytesseract to enable text extraction.",
                source=filename,
                modality="image",
                metadata={"type": "image", "ocr_available": False},
            )
        ]

    try:
        image = Image.open(io.BytesIO(file_content))
        text = pytesseract.image_to_string(image)
    except Exception as e:
        logger.warning(f"OCR failed for {filename}: {e}. Tesseract may not be installed.")
        text = ""

    if not text or not text.strip():
        # Even without OCR text, store the image metadata as a chunk
        return [
            ProcessedChunk(
                chunk_index=0,
                content=f"[Medical Image: {filename}] — No readable text extracted via OCR. "
                        "This image was uploaded for reference.",
                source=filename,
                modality="image",
                metadata={"type": "image", "ocr_text_found": False},
            )
        ]

    # Chunk the OCR text
    text_chunks = chunker.chunk_text(text)
    chunks = []
    for idx, content in enumerate(text_chunks):
        chunks.append(
            ProcessedChunk(
                chunk_index=idx,
                content=content,
                source=filename,
                modality="image",
                metadata={"type": "image", "ocr_text_found": True},
            )
        )
    return chunks


def parse_dicom(file_content: bytes, filename: str) -> List[ProcessedChunk]:
    """
    Extract text metadata from a DICOM file.
    Focuses on patient-safe fields: study description, modality, body part,
    institution, referring physician.
    """
    try:
        import pydicom
    except ImportError:
        logger.error("pydicom not installed. Run: pip install pydicom")
        return [
            ProcessedChunk(
                chunk_index=0,
                content=f"[DICOM file: {filename}] — pydicom not installed.",
                source=filename,
                modality="dicom",
                metadata={"type": "dicom", "parse_available": False},
            )
        ]

    try:
        ds = pydicom.dcmread(io.BytesIO(file_content))
    except Exception as e:
        logger.error(f"Failed to read DICOM {filename}: {e}")
        return [
            ProcessedChunk(
                chunk_index=0,
                content=f"[DICOM file: {filename}] — Failed to parse file.",
                source=filename,
                modality="dicom",
                metadata={"type": "dicom", "error": str(e)},
            )
        ]

    # Extract safe metadata fields
    fields = {
        "Study Description": getattr(ds, "StudyDescription", "N/A"),
        "Series Description": getattr(ds, "SeriesDescription", "N/A"),
        "Modality": getattr(ds, "Modality", "N/A"),
        "Body Part Examined": getattr(ds, "BodyPartExamined", "N/A"),
        "Institution Name": getattr(ds, "InstitutionName", "N/A"),
        "Manufacturer": getattr(ds, "Manufacturer", "N/A"),
        "Study Date": getattr(ds, "StudyDate", "N/A"),
        "Image Comments": getattr(ds, "ImageComments", "N/A"),
    }

    text_lines = [f"DICOM Metadata for: {filename}"]
    for key, val in fields.items():
        if val and val != "N/A":
            text_lines.append(f"  {key}: {val}")

    content = "\n".join(text_lines)

    return [
        ProcessedChunk(
            chunk_index=0,
            content=content,
            source=filename,
            modality="dicom",
            metadata={
                "type": "dicom",
                **{k.lower().replace(" ", "_"): v for k, v in fields.items() if v != "N/A"},
            },
        )
    ]
