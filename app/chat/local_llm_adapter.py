import base64
import io
import logging
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)

class LocalLLMAdapter:
    """
    Unified adapter for Gemma 4 local inference via Ollama or vLLM.
    Strictly restricted to localhost for data security.
    """

    def __init__(self):
        self.timeout = httpx.Timeout(120.0, connect=10.0)

    def _validate_localhost(self, url: str):
        """Security check to ensure traffic stays on the local machine."""
        parsed = urlparse(url)
        hostname = parsed.hostname
        if hostname not in ("localhost", "127.0.0.1"):
            raise ValueError(
                f"Security Violation: Local LLM traffic must be restricted to localhost. "
                f"Attempted to connect to: {hostname}"
            )

    def _resize_image(self, base64_str: str, size: int = 1120) -> str:
        """
        Optimizes medical images/scans to Gemma 4's native resolution.
        Reduces payload size and improves inference speed.
        """
        try:
            image_data = base64.b64decode(base64_str)
            img = Image.open(io.BytesIO(image_data))
            
            # Maintain aspect ratio
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85) # JPEG is more compact for transmission
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
        except Exception as e:
            logger.warning(f"Image optimization failed, sending original: {e}")
            return base64_str

    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: str, 
        images: Optional[List[str]] = None
    ) -> str:
        """Calls the configured local provider (Ollama or vLLM)."""
        
        # Prepare multimodal data if present
        optimized_images = []
        if images:
            optimized_images = [self._resize_image(img) for img in images]

        if settings.LLM_PROVIDER == "ollama":
            return await self._call_ollama(prompt, system_prompt, optimized_images)
        elif settings.LLM_PROVIDER == "vllm":
            return await self._call_vllm(prompt, system_prompt, optimized_images)
        else:
            raise ValueError(f"Unsupported local provider: {settings.LLM_PROVIDER}")

    async def _call_ollama(self, prompt: str, system_prompt: str, images: List[str]) -> str:
        url = f"{settings.OLLAMA_BASE_URL}/api/chat"
        self._validate_localhost(url)

        payload = {
            "model": settings.LOCAL_LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt, "images": images if images else []}
            ],
            "stream": False,
            "options": {
                "num_ctx": settings.LOCAL_LLM_MAX_CTX,
                "temperature": 0.2
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")

    async def _call_vllm(self, prompt: str, system_prompt: str, images: List[str]) -> str:
        url = f"{settings.VLLM_BASE_URL}/v1/chat/completions"
        self._validate_localhost(url)

        # vLLM/OpenAI vision format
        content = [{"type": "text", "text": prompt}]
        for img_b64 in images:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
            })

        payload = {
            "model": settings.LOCAL_LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            "max_tokens": 1024,
            "temperature": 0.2
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

# Singleton
local_llm_adapter = LocalLLMAdapter()
