import dataclasses

from src.common.class_with_creator import ClassWithCreator

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Callable, Dict, Optional, List
from enum import Enum, auto

import logging

logger = logging.getLogger(__name__)


class ChatStreamResponseType(Enum):
    THINKING = auto()
    CONTENT = auto()
    TOOL = auto()


@dataclass
class ToolCall:
    name: str
    func: Callable
    arguments: dict


@dataclass
class ChatVerboseResponse:
    response: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    tool_calls: List[ToolCall] = dataclasses.field(default_factory=list)
    thinking: str = ""


@dataclass
class ChatStreamResponse:
    content_type: ChatStreamResponseType
    data: Optional[str] = dataclasses.field(default=None)
    tool_calls: List[ToolCall] = dataclasses.field(default_factory=list)


class ChatProvider(ABC, ClassWithCreator):
    def __init__(self):
        self._json_schema = None
        self._tools = {}

    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, str]],
    ) -> AsyncGenerator[ChatStreamResponse, None]:
        pass

    def set_output_json_schema(self, schema):
        self._json_schema = schema

    def add_tool_call(self, func):
        tool_schema = func._tool_schema
        tool_name = tool_schema["function"]["name"]
        if tool_name in self._tools:
            logger.warning(f"Overrided tool with name: {tool_name}")
        self._tools[tool_name] = func

    @abstractmethod
    async def chat_response_only(self, messages: List[Dict[str, str]]) -> str:
        pass

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]]) -> ChatVerboseResponse:
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
