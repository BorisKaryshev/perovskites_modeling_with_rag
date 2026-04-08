from src.common.class_with_creator import ClassWithCreator
from src.common.workers_pool import WorkersPool
from src.document_store import DBSchema
from src.llm_providers import ChatVerboseResponse, ChatStreamResponse

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Optional, List, Tuple


class ChatRequester(ABC, ClassWithCreator, WorkersPool):
    def __init__(self):
        self._json_schema = None

    def set_output_json_schema(self, schema):
        self._json_schema = schema

    @abstractmethod
    async def send_request(
        self,
        query: str,
        records_with_scores: List[Tuple[float, DBSchema]],
        history: List[Dict[str, str]],
    ) -> str:
        pass

    @abstractmethod
    async def send_request_verbose(
        self,
        query: str,
        records_with_scores: List[Tuple[float, DBSchema]],
        history: List[Dict[str, str]],
    ) -> ChatVerboseResponse:
        pass

    @abstractmethod
    async def send_request_stream(
        self,
        query: str,
        records_with_scores: List[Tuple[float, DBSchema]],
        history: List[Dict[str, str]],
    ) -> AsyncGenerator[ChatStreamResponse, None]:
        pass

    @staticmethod
    def create(
        name: str,
        *args,
        **kwargs,
    ) -> "ChatRequester":
        return ChatRequester._create(name, *args, **kwargs)
