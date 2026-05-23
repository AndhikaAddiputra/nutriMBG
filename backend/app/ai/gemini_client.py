from typing import Any, Dict, List

import httpx

from app.ai.base import BaseAIClient
from app.ai.cache import get_ai_cache
from app.ai.utils import extract_json_payload
from app.core.settings import settings


class GeminiClient(BaseAIClient):
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY belum diatur.")
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.base_url = settings.gemini_base_url.rstrip("/")
        self._cache = get_ai_cache()

    async def generate(self, prompt: str) -> str:
        cached = self._cache.get(prompt)
        if cached is not None:
            return cached

        url = f"{self.base_url}/models/{self.model}:generateContent"
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
        }
        params = {"key": self.api_key}
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                response = await client.post(url, json=payload, params=params)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                message = exc.response.text
                try:
                    message = exc.response.json().get("error", {}).get("message", message)
                except ValueError:
                    pass
                raise RuntimeError(f"Gemini API error {exc.response.status_code}: {message}") from exc
            except httpx.RequestError as exc:
                raise RuntimeError(f"Gemini API request failed: {exc}") from exc

        data = response.json()
        candidates: List[Dict[str, Any]] = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini tidak mengembalikan kandidat jawaban.")

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            raise RuntimeError("Gemini tidak mengembalikan konten jawaban.")

        text = parts[0].get("text", "")
        if not text:
            raise RuntimeError("Gemini mengembalikan konten kosong.")

        self._cache.set(prompt, text)
        return text

    async def generate_json(self, prompt: str) -> Any:
        text = await self.generate(prompt)
        return extract_json_payload(text)
