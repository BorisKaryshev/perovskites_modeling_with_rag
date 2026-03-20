from src.common.class_with_creator import ClassWithCreator
from src.common.workers_pool import WorkersPool
from src.common.document_type import DocumentType

import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path


class DocumentParser(ABC, ClassWithCreator, WorkersPool):
    @abstractmethod
    async def parse_document(self, document_path: Path) -> str:
        pass

    async def get_doc_creation_date(self, document_path: Path) -> datetime:
        creation_timestamp = os.path.getctime(document_path)
        return datetime.fromtimestamp(creation_timestamp)

    async def get_doc_type(self, document_path: Path) -> DocumentType:
        for i in document_path.suffixes:
            i = i.strip(".")
            try:
                return DocumentType(i)
            except ValueError:
                pass

        return DocumentType.UNKNONW

    @staticmethod
    def create(
        instance_name: str,
        *args,
        **kwargs,
    ) -> "DocumentParser":
        return DocumentParser._create(instance_name, *args, **kwargs)
