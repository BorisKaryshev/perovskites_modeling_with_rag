from abc import ABC, abstractmethod
from typing import Dict, List

from src.common.class_with_creator import ClassWithCreator


class ChatProvider(ABC, ClassWithCreator):
    @abstractmethod
    async def chat_response_only(self, messages: List[Dict[str, str]]) -> str:
        pass

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]]) -> dict:
        pass

    @staticmethod
    def create(
        name: str,
        model: str,
        base_url: str,
        *args,
        **kwargs,
    ) -> "ChatProvider":
        return ChatProvider._create(name, model, base_url, *args, **kwargs)


class EmbedderProvider(ABC, ClassWithCreator):
    @abstractmethod
    async def embed(self, query: str) -> List[float]:
        pass

    @staticmethod
    def create(
        name: str,
        model: str,
        base_url: str,
        *args,
        **kwargs,
    ) -> "EmbedderProvider":
        return EmbedderProvider._create(name, model, base_url, *args, **kwargs)
