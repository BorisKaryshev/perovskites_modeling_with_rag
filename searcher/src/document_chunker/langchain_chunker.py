from src.common.workers_pool import WorkersPool
from .interface import DocumentChunker

from typing import override, Tuple, List
from enum import Enum
import logging

from langchain_core.documents import Document
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)

logger = logging.getLogger(__name__)


class LangchainChunkerType(Enum):
    def __new__(cls, value, chunker_type):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.chunker_type = chunker_type
        return obj

    chunker_type: type

    RECURSIVE_CHARACTER = ("recursive_character", RecursiveCharacterTextSplitter)
    CHARACTER_TEXT = ("character_text", CharacterTextSplitter)


class LangchainChunker(DocumentChunker):
    def __init__(
        self,
        chunker_name: str,
        *args,
        **kwargs,
    ):
        super().__init__()
        logger.info("Created LangchainChunker")

        self._chunker_type = LangchainChunkerType(chunker_name).chunker_type
        self._text_splitter_args = (args, kwargs)

    @staticmethod
    def _chunk_document_impl(
        text_splitter: type,
        data: str,
        text_splitter_creation_args=None,
    ) -> List[Tuple[int, str]]:
        creator = None
        if text_splitter_creation_args:
            creator = lambda: text_splitter(
                *text_splitter_creation_args[0], **text_splitter_creation_args[1]
            )
        instance = WorkersPool.get_class_instance(
            text_splitter,
            creator,
        )

        docs = [Document(data)]
        return instance.split_documents(docs)

    @override
    async def chunk_document(self, data: str) -> List[Tuple[int, str]]:
        splitted = await self.apply(
            self._chunk_document_impl,
            self._chunker_type,
            data,
            self._text_splitter_args,
        )

        return [(idx, i.page_content) for (idx, i) in enumerate(splitted)]
