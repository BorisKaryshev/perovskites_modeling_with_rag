from abc import ABC, abstractmethod
from typing import List, Tuple

from src.common.class_with_creator import ClassWithCreator
from src.common.workers_pool import WorkersPool


class DocumentChunker(ABC, ClassWithCreator, WorkersPool):
    @abstractmethod
    async def chunk_document(self, data: str) -> List[Tuple[int, str]]:
        pass

    @staticmethod
    def create(
        name: str,
        *args,
        **kwargs,
    ) -> "DocumentChunker":
        return DocumentChunker._create(name, *args, **kwargs)
