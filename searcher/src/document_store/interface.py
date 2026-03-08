from src.common.class_with_creator import ClassWithCreator
from src.common.document_type import DocumentType
from src.common.workers_pool import WorkersPool

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, TYPE_CHECKING
from pydantic import BaseModel, NonNegativeInt
from datetime import datetime
from pathlib import Path
import hashlib

if TYPE_CHECKING:
    from qdrant_client.http.models import Filter


class DBSchema(BaseModel):
    payload: str
    chunk_idx: NonNegativeInt
    doc_path: Path
    doc_type: DocumentType
    created: datetime

    @property
    def key(self):
        return self.payload

    @property
    def id(self):
        return hash(self)

    def __hash__(self):
        payload_hash = hashlib.md5(self.payload.encode()).digest()
        payload_hash = int.from_bytes(payload_hash)
        doc_path_hash = hashlib.md5(f"{self.doc_path}".encode()).digest()
        doc_path_hash = int.from_bytes(doc_path_hash)
        created_hash = hashlib.md5(f"{self.created}".encode()).digest()
        created_hash = int.from_bytes(created_hash)

        h = (
            payload_hash + doc_path_hash + created_hash
        ) & 0xFFFFFFFFFFFFFFFF  # Making int unsigned
        return h


class DocumentMustBeDeletedFilter(ABC):
    @abstractmethod
    async def __call__(self, record: DBSchema) -> bool:
        pass

    async def create_filter_for_qdrant(self) -> Optional["Filter"]:
        return None


class DocumentStore(ABC, ClassWithCreator, WorkersPool):
    @abstractmethod
    async def add_record(self, record: DBSchema) -> None:
        pass

    @abstractmethod
    async def search_by_query(self, query: str) -> List[Tuple[float, DBSchema]]:
        pass

    @abstractmethod
    async def delete_document(self, delete_filter: DocumentMustBeDeletedFilter):
        pass

    @staticmethod
    def create(
        instance_name: str,
        *args,
        **kwargs,
    ) -> "DocumentStore":
        return DocumentStore._create(instance_name, *args, **kwargs)
