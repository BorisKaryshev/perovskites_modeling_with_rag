from .interface import EntryPoint

from src.document_store import DocumentMustBeDeletedFilter, DocumentStore, DBSchema

import asyncio
from argparse import ArgumentParser, Namespace
from pathlib import Path
import time
from typing import Optional
import logging

from qdrant_client.models import Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)


class DeleteFileFilter(DocumentMustBeDeletedFilter):
    def __init__(self, filepath: Path):
        self._path = Path(filepath).absolute()

    async def __call__(self, record: DBSchema) -> bool:
        return record.doc_path == self._path

    async def create_filter_for_qdrant(self) -> Optional["Filter"]:
        return Filter(
            must=[
                FieldCondition(
                    key="doc_path",
                    match=MatchValue(
                        value=str(self._path),
                    ),
                ),
            ]
        )


class RemoveFilesEntryPoint(EntryPoint):
    def __init__(self, args: Namespace):
        super().__init__(args)

        self._files_to_delete = [Path(i).absolute() for i in args.files_to_delete]
        self._n_of_files_to_add_in_parallel = args.n_of_files_to_add_in_parallel

        self._store = DocumentStore.create(
            self._config["document_store"]["type"],
            **self._config["document_store"]["options"],
        )

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        parser.add_argument("files_to_delete", nargs="+", type=Path)
        parser.add_argument(
            "-n", "--n_of_files_to_add_in_parallel", type=int, default=3, required=False
        )

    async def _worker(self, queue: asyncio.Queue):
        path = await queue.get()
        while path is not None:
            begin = time.time()

            delete_filter = DeleteFileFilter(path)
            await self._store.delete_document(delete_filter)

            end = time.time()
            logger.info(
                f"Deleting file with path '{path}' took: {int((end - begin) * 1000)} ms"
            )

            path = await queue.get()

    async def run(self) -> None:
        logger.debug("entery_point started")
        queue = asyncio.Queue(self._n_of_files_to_add_in_parallel)

        async with asyncio.TaskGroup() as tg:
            for _ in range(self._n_of_files_to_add_in_parallel):
                tg.create_task(self._worker(queue))

            for i in self._files_to_delete:
                await queue.put(i)

            for _ in range(self._n_of_files_to_add_in_parallel):
                await queue.put(None)
