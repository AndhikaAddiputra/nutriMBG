from typing import Any

import httpx

from app.ai.base import BaseAIClient
from app.ai.cache import get_ai_cache
from app.ai.utils import extract_json_payload
from app.core.settings import settings


class OllamaClient(BaseAIClient):
    def __init__(self) -> None:
        self.base_url = settings.ollama_host.rstrip("/")
        self.model = settings.ollama_model
        self._cache = get_ai_cache()

    async def generate(self, prompt: str) -> str:
        cached = self._cache.get(prompt)
        if cached is not None:
            return cached

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": f"{prompt}\n\nRespond ONLY with valid JSON. No explanation.",
            "stream": False,
            "options": {"temperature": 0.2},
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                message = exc.response.text
                raise RuntimeError(f"Ollama API error {exc.response.status_code}: {message}") from exc
            except httpx.RequestError as exc:
                raise RuntimeError(f"Ollama API request failed: {exc}") from exc

        data = response.json()
        text = data.get("response", "")
        if not text:
            raise RuntimeError("Ollama mengembalikan konten kosong.")

        self._cache.set(prompt, text)
        return text

    async def generate_json(self, prompt: str) -> Any:
        text = await self.generate(prompt)
        return extract_json_payload(text)
