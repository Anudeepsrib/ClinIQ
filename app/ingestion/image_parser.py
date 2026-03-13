"""
Image and DICOM parsers for multimodal ingestion.

- Images (PNG, JPEG, TIFF, BMP): OCR text extraction + raw bytes for native Gemini embedding
- DICOM (.dcm): Metadata text extraction + pixel data as image bytes
"""

import io
import logging
from typing import List

from app.schemas.models import ProcessedChunk
from app.ingestion.chunker import ContentChunker

logger = logging.getLogger(__name__)
chunker = ContentChunker()


def _detect_mime_type(filename: str) -> str:
    """Map filename extension to MIME type."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "tiff": "image/tiff",
        "bmp": "image/bmp",
    }.get(ext, "image/png")


def parse_image(file_content: bytes, filename: str) -> List[ProcessedChunk]:
    """
    Extract text from an image using OCR (Tesseract) and preserve raw bytes
    for native multimodal embedding via Gemini Embedding 2.
    """
    mime_type = _detect_mime_type(filename)
    ocr_text = ""

    try:
        from PIL import Image
        import pytesseract
        image = Image.open(io.BytesIO(file_content))
        ocr_text = pytesseract.image_to_string(image).strip()
    except ImportError:
        logger.warning("Pillow or pytesseract not installed — OCR skipped")
    except Exception as e:
        logger.warning(f"OCR failed for {filename}: {e}")

    content = ocr_text if ocr_text else (
        f"[Medical Image: {filename}] — No readable text extracted via OCR. "
        "This image was uploaded for reference."
    )

    # If OCR produced long text, chunk it; otherwise single chunk
    if ocr_text and len(ocr_text) > 500:
        text_chunks = chunker.chunk_text(ocr_text)
        chunks = []
        for idx, text_content in enumerate(text_chunks):
            chunks.append(
                ProcessedChunk(
                    chunk_index=idx,
                    content=text_content,
                    source=filename,
                    modality="image",
                    embedding_modality="image",
                    raw_bytes=file_content if idx == 0 else None,  # attach bytes to first chunk only
                    mime_type=mime_type if idx == 0 else None,
                    metadata={"type": "image", "ocr_text_found": True},
                )
            )
        return chunks

    return [
        ProcessedChunk(
            chunk_index=0,
            content=content,
            source=filename,
            modality="image",
            embedding_modality="image",
            raw_bytes=file_content,
            mime_type=mime_type,
            metadata={"type": "image", "ocr_text_found": bool(ocr_text)},
        )
    ]


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

    # Try to extract pixel data as PNG for native image embedding
    image_bytes = None
    try:
        if hasattr(ds, "pixel_array"):
            from PIL import Image
            import numpy as np
            arr = ds.pixel_array
            if arr.dtype != np.uint8:
                arr = ((arr - arr.min()) / max(arr.max() - arr.min(), 1) * 255).astype(np.uint8)
            img = Image.fromarray(arr)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            image_bytes = buf.getvalue()
    except Exception as e:
        logger.warning(f"Could not extract pixel data from DICOM {filename}: {e}")

    return [
        ProcessedChunk(
            chunk_index=0,
            content=content,
            source=filename,
            modality="dicom",
            embedding_modality="image" if image_bytes else "text",
            raw_bytes=image_bytes,
            mime_type="image/png" if image_bytes else None,
            metadata={
                "type": "dicom",
                **{k.lower().replace(" ", "_"): v for k, v in fields.items() if v != "N/A"},
            },
        )
    ]
