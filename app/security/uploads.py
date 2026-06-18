"""Upload validation helpers for document ingestion endpoints."""

from __future__ import annotations

import re
from pathlib import PurePosixPath, PureWindowsPath

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_MIME_TYPES = {
    "pdf": {"application/pdf"},
    "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    "xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    "xls": {"application/vnd.ms-excel", "application/octet-stream"},
    "png": {"image/png"},
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
    "tiff": {"image/tiff"},
    "bmp": {"image/bmp"},
    "dcm": {"application/dicom", "application/octet-stream"},
    "mp3": {"audio/mpeg", "audio/mp3"},
    "wav": {"audio/wav", "audio/x-wav"},
    "m4a": {"audio/mp4", "audio/m4a"},
    "flac": {"audio/flac"},
    "ogg": {"audio/ogg"},
    "mp4": {"video/mp4"},
    "mov": {"video/quicktime", "video/mov"},
    "avi": {"video/x-msvideo", "video/avi"},
    "webm": {"video/webm"},
}

SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._ -]+")


def sanitize_filename(filename: str | None) -> str:
    """Return a safe basename or raise if the filename is unsafe."""
    if not filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename")

    if "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filenames must not include path separators",
        )

    posix_name = PurePosixPath(filename).name
    windows_name = PureWindowsPath(filename).name
    if filename not in {posix_name, windows_name}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filenames must not include path components",
        )

    cleaned = SAFE_FILENAME_RE.sub("_", filename).strip(" .")
    if not cleaned or cleaned in {".", ".."} or cleaned.startswith("."):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

    if len(cleaned) > 180:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is too long")

    return cleaned


def validate_upload_metadata(file: UploadFile) -> str:
    """Validate filename, extension, and MIME type. Return sanitized filename."""
    safe_name = sanitize_filename(file.filename)
    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if ext not in settings.allowed_upload_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '.{ext or 'unknown'}'",
        )

    allowed_mimes = ALLOWED_MIME_TYPES.get(ext, set())
    content_type = (file.content_type or "").lower()
    if allowed_mimes and content_type and content_type not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported MIME type '{content_type}' for '.{ext}'",
        )

    return safe_name


async def read_limited_upload(file: UploadFile) -> bytes:
    """Read an upload while enforcing the configured maximum size."""
    max_bytes = settings.MAX_UPLOAD_BYTES
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Upload exceeds maximum size of {max_bytes} bytes",
        )
    return content
