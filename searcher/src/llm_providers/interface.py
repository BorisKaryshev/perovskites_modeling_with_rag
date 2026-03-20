from src.common.class_with_creator import ClassWithCreator

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Dict, List
from enum import Enum, auto


class ChatStreamResponseType(Enum):
    THINKING = auto()
    CONTENT = auto()


@dataclass
class ChatStreamResponse:
    data: str
    content_type: ChatStreamResponseType


class ChatProvider(ABC, ClassWithCreator):
    def __init__(self):
        self._json_schema = None

    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, str]],
    ) -> AsyncGenerator[ChatStreamResponse, None]:
        pass

    def set_output_json_schema(self, schema):
        self._json_schema = schema

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
