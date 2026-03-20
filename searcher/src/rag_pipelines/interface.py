from src.common.class_with_creator import ClassWithCreator
from src.common.workers_pool import WorkersPool
from src.document_store import DBSchema

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from pydantic import BaseModel


class RagResponse(BaseModel):
    user_query: str
    response: str
    references: List[Path]

    @staticmethod
    def filled_response_examples() -> List["RagResponse"]:
        return [
            RagResponse(user_query="Say hello", response="Hello", references=[]),
            RagResponse(
                user_query="Who is putin",
                response="Vladimir Putin is a Russian political leader.\n\n* Born: 1952 in Leningrad\n* Former KGB officer\n* President of Russia since 2000 (with a break in 2008–2012)\n\nHe is one of the most influential figures in global politics.",
                references=[Path("/stored_files/History_of_Russia.pdf")],
            ),
            RagResponse(
                user_query="Find info about aliens invading moscow in 1958",
                response="Provided documents do not contain answer",
                references=[],
            ),
        ]


class RagPipeline(ABC, ClassWithCreator, WorkersPool):
    @abstractmethod
    async def add_documents(
        self,
        files: List[Path],
        n_of_parallel_added_files: int = 2,
    ):
        pass

    @abstractmethod
    async def add_document(self, file: Path):
        pass

    @abstractmethod
    async def delete_document(self, path: Path):
        pass

    @abstractmethod
    async def document_exists(self, document_path: Path) -> bool:
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        history: List[Dict[str, str]],
    ) -> RagResponse:
        pass

    @abstractmethod
    async def retrieve_docs(
        self,
        query: str,
        limit: Optional[int] = None,
    ) -> List[Tuple[float, DBSchema]]:
        pass

    @staticmethod
    def create(
        type_name: str,
        *args,
        **kwargs,
    ) -> "RagPipeline":
        return RagPipeline._create(type_name, *args, **kwargs)
