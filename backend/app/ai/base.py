from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAIClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        ...

    @abstractmethod
    async def generate_json(self, prompt: str) -> Any:
        ...
