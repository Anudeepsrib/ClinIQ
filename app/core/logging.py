"""Logging helpers that redact secrets and common PHI patterns."""

import logging
import re
from typing import Any

SECRET_PATTERNS = [
    re.compile(r"(sk-[A-Za-z0-9_\-]{12,})"),
    re.compile(r"(AIza[0-9A-Za-z_\-]{20,})"),
    re.compile(r"(ls__[A-Za-z0-9_\-]{8,})"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)=([^&\s]+)"),
]

PHI_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    re.compile(r"\bMRN[-:\s]?[A-Za-z0-9-]{4,}\b", re.IGNORECASE),
]


def redact_text(value: Any) -> str:
    """Return a string with obvious secrets and PHI-like values redacted."""
    text = str(value)
    for pattern in SECRET_PATTERNS:
        if pattern.groups >= 2:
            text = pattern.sub(lambda m: f"{m.group(1)}=<redacted>", text)
        else:
            text = pattern.sub("<redacted-secret>", text)
    for pattern in PHI_PATTERNS:
        text = pattern.sub("<redacted-phi>", text)
    return text


class RedactingFilter(logging.Filter):
    """Sanitize log messages before handlers emit them."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_text(record.getMessage())
        record.args = ()
        return True


def configure_logging() -> None:
    """Attach a redaction filter to root logging handlers."""
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=logging.INFO)

    redactor = RedactingFilter()
    for handler in root.handlers:
        if not any(isinstance(existing, RedactingFilter) for existing in handler.filters):
            handler.addFilter(redactor)
