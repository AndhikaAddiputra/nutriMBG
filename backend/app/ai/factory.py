from typing import Optional

from app.ai.base import BaseAIClient
from app.ai.gemini_client import GeminiClient
from app.ai.ollama_client import OllamaClient
from app.core.settings import settings


_PROVIDER_MAP = {
    "gemini": GeminiClient,
    "ollama": OllamaClient,
}


def get_ai_client(provider: Optional[str] = None) -> BaseAIClient:
    provider = (provider or settings.recommender_provider).lower()
    client_class = _PROVIDER_MAP.get(provider)
    if client_class is None:
        available = list(_PROVIDER_MAP)
        raise ValueError(f"Unknown AI provider '{provider}'. Available: {available}")
    return client_class()
