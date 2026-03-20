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


class ExampleEntryPoint(EntryPoint):
    def __init__(self, args: Namespace):
        super().__init__(args)
        self._file_to_chunk = args.file_to_chunk

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        parser.add_argument("file_to_chunk", type=Path)

    async def run(self) -> None:
        n_of_workers = self._config.get("common", {}).get("n_of_workers")
        if n_of_workers:
            async with await WorkersPool.create_pool(n_of_workers):
                return await self._run_impl()
        return await self._run_impl()

    async def _run_impl(self) -> None:
        logger.debug("entery_point started")
        parser = DocumentParser.create(self._config["document_parser"]["type"])
        chunker = DocumentChunker.create(
            self._config["document_chunker"]["type"],
            **self._config["document_chunker"]["options"],
        )
        store = DocumentStore.create(
            self._config["document_store"]["type"],
            **self._config["document_store"]["options"],
        )

        begin = time.time()
        content = await parser.parse_document(self._file_to_chunk)
        chunked = await chunker.chunk_document(content)

        async with asyncio.TaskGroup() as tg:
            for idx, payload in chunked:
                record = DBSchema(
                    payload=payload,
                    chunk_idx=idx,
                    doc_path=self._file_to_chunk,
                    doc_type=(await parser.get_doc_type(self._file_to_chunk)),
                    created=(await parser.get_doc_creation_date(self._file_to_chunk)),
                )
                tg.create_task(store.add_record(record))

        end = time.time()
        logger.info(
            f"Uploading markdown file in {len(chunked)} chunks took: {int((end - begin) * 1000)} ms"
        )
        query = input("Your search query: ")

        result = await store.search_by_query(query)

        logger.info(f"Got from store:")
        for score, record in result[:1]:
            print(score)
            print(record.payload)
