"""
Gemini Multimodal Embeddings — unified embedding layer for ClinIQ.

Wraps Google's Gemini Embedding 2 model to provide native multimodal
embeddings (text, images, PDFs, audio, video) in a single vector space.
Falls back to OpenAI text-embedding-3-small when EMBEDDING_PROVIDER=openai.

API ref: https://ai.google.dev/gemini-api/docs/embeddings
"""

import base64
import logging
from typing import List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiMultimodalEmbeddings:
    """
    Multimodal embedding service backed by Gemini Embedding 2.

    Supports: text, image (PNG/JPEG), PDF (≤6 pages), audio (≤120s), video (≤120s).
    All modalities are embedded into a single 3072-dim vector space.
    Implements LangChain-compatible embed_documents / embed_query for drop-in use.
    """

    def __init__(self):
        self._provider = settings.EMBEDDING_PROVIDER
        self._dimensions = settings.EMBEDDING_DIMENSIONS
        self._gemini_client = None
        self._openai_fallback = None

    def _get_gemini_client(self):
        if self._gemini_client is None:
            from google import genai
            self._gemini_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        return self._gemini_client

    def _get_openai_fallback(self):
        if self._openai_fallback is None:
            from langchain_openai import OpenAIEmbeddings
            self._openai_fallback = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                api_key=settings.OPENAI_API_KEY,
            )
        return self._openai_fallback

    # ------------------------------------------------------------------
    # Text embeddings (LangChain-compatible interface)
    # ------------------------------------------------------------------

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text documents. LangChain-compatible."""
        if self._provider == "openai":
            return self._get_openai_fallback().embed_documents(texts)

        client = self._get_gemini_client()
        result = client.models.embed_content(
            model="gemini-embedding-exp-03-07",
            contents=texts,
            config={
                "output_dimensionality": self._dimensions,
            },
        )
        return [e.values for e in result.embeddings]

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string. LangChain-compatible."""
        if self._provider == "openai":
            return self._get_openai_fallback().embed_query(query)

        client = self._get_gemini_client()
        result = client.models.embed_content(
            model="gemini-embedding-exp-03-07",
            contents=query,
            config={
                "output_dimensionality": self._dimensions,
            },
        )
        return result.embeddings[0].values

    # ------------------------------------------------------------------
    # Multimodal embeddings (Gemini-only)
    # ------------------------------------------------------------------

    def embed_image(self, image_bytes: bytes, mime_type: str = "image/png") -> List[float]:
        """Embed a raw image natively (no OCR needed)."""
        if self._provider == "openai":
            logger.warning("OpenAI does not support image embeddings, returning empty vector")
            return [0.0] * self._dimensions

        from google.genai import types

        client = self._get_gemini_client()
        result = client.models.embed_content(
            model="gemini-embedding-exp-03-07",
            contents=types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            config={
                "output_dimensionality": self._dimensions,
            },
        )
        return result.embeddings[0].values

    def embed_pdf(self, pdf_bytes: bytes) -> List[float]:
        """Embed a PDF natively (up to 6 pages)."""
        if self._provider == "openai":
            logger.warning("OpenAI does not support PDF embeddings, returning empty vector")
            return [0.0] * self._dimensions

        from google.genai import types

        client = self._get_gemini_client()
        result = client.models.embed_content(
            model="gemini-embedding-exp-03-07",
            contents=types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            config={
                "output_dimensionality": self._dimensions,
            },
        )
        return result.embeddings[0].values

    def embed_audio(self, audio_bytes: bytes, mime_type: str = "audio/mp3") -> List[float]:
        """Embed audio natively (up to 120 seconds)."""
        if self._provider == "openai":
            logger.warning("OpenAI does not support audio embeddings, returning empty vector")
            return [0.0] * self._dimensions

        from google.genai import types

        client = self._get_gemini_client()
        result = client.models.embed_content(
            model="gemini-embedding-exp-03-07",
            contents=types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            config={
                "output_dimensionality": self._dimensions,
            },
        )
        return result.embeddings[0].values

    def embed_video(self, video_bytes: bytes, mime_type: str = "video/mp4") -> List[float]:
        """Embed video natively (up to 120 seconds)."""
        if self._provider == "openai":
            logger.warning("OpenAI does not support video embeddings, returning empty vector")
            return [0.0] * self._dimensions

        from google.genai import types

        client = self._get_gemini_client()
        result = client.models.embed_content(
            model="gemini-embedding-exp-03-07",
            contents=types.Part.from_bytes(data=video_bytes, mime_type=mime_type),
            config={
                "output_dimensionality": self._dimensions,
            },
        )
        return result.embeddings[0].values


# Module-level singleton
gemini_embeddings = GeminiMultimodalEmbeddings()
