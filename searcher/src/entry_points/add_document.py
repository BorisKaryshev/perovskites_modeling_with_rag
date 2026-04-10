from .interface import EntryPoint
from src.common.workers_pool import WorkersPool

from src.document_chunker import DocumentChunker
from src.document_parser import DocumentParser
from src.document_store import DocumentStore, DBSchema

import asyncio
from argparse import ArgumentParser, Namespace
from pathlib import Path
import time
import logging

logger = logging.getLogger(__name__)


class AddDocumentEntryPoint(EntryPoint):
    def __init__(self, args: Namespace):
        super().__init__(args)

        self._files_to_add = [Path(i).absolute() for i in args.files_to_add]
        self._n_of_parallel_requests = args.n_of_parallel_requests

        self._parser = DocumentParser.create(self._config["document_parser"]["type"])
        self._chunker = DocumentChunker.create(
            self._config["document_chunker"]["type"],
            **self._config["document_chunker"]["options"],
        )
        self._store = DocumentStore.create(
            self._config["document_store"]["type"],
            **self._config["document_store"]["options"],
        )

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "-n", "--n_of_parallel_requests", type=int, default=3, required=False
        )
        parser.add_argument("files_to_add", nargs="+", type=Path)

    async def add_file(self, file: Path):
        begin = time.time()
        content = await self._parser.parse_document(file)
        chunked = await self._chunker.chunk_document(content)

        async with asyncio.TaskGroup() as tg:
            for idx, payload in chunked:
                record = DBSchema(
                    payload=payload,
                    chunk_idx=idx,
                    doc_path=file,
                    doc_type=(await self._parser.get_doc_type(file)),
                    created=(await self._parser.get_doc_creation_date(file)),
                )
                tg.create_task(self._store.add_record(record))

        end = time.time()
        logger.info(
            f"Uploading file '{file}' in {len(chunked)} chunks took: {int((end - begin) * 1000)} ms"
        )

    async def _worker(self, path: Path, semathore: asyncio.Semaphore):
        async with semathore:
            await self.add_file(path)

    async def _run_impl(self) -> None:
        logger.debug("entery_point started")

        semathore = asyncio.Semaphore(self._n_of_parallel_requests)

        tasks = [self._worker(p, semathore) for p in self._files_to_add]

        asyncio.gather(*tasks)

    async def run(self) -> None:
        n_of_workers = self._config.get("common", {}).get("n_of_workers")
        if n_of_workers:
            async with await WorkersPool.create_pool(n_of_workers):
                return await self._run_impl()
        return await self._run_impl()
