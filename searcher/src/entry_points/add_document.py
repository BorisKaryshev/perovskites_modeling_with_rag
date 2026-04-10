from .interface import EntryPoint
from src.common.workers_pool import WorkersPool

from src.rag_pipelines import RagPipeline

import asyncio
from argparse import ArgumentParser, Namespace
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AddDocumentEntryPoint(EntryPoint):
    def __init__(self, args: Namespace):
        super().__init__(args)

        self._files_to_add = [Path(i).absolute() for i in args.files_to_add]
        self._n_of_parallel_requests = args.n_of_parallel_requests

        self._rag = RagPipeline.create(
            self._config["rag"].pop("type"),
            config=self._config,
        )

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "-n", "--n_of_parallel_requests", type=int, default=3, required=False
        )
        parser.add_argument("files_to_add", nargs="+", type=Path)

    async def add_file(self, file: Path, semathore: asyncio.Semaphore):
        async with semathore:
            await self._rag.add_document(file)

    async def _run_impl(self) -> None:

        semathore = asyncio.Semaphore(self._n_of_parallel_requests)

        tasks = [self.add_file(p, semathore) for p in self._files_to_add]

        await asyncio.gather(*tasks)

    async def run(self) -> None:
        n_of_workers = self._config.get("common", {}).get("n_of_workers")
        if n_of_workers:
            async with await WorkersPool.create_pool(n_of_workers):
                return await self._run_impl()
        return await self._run_impl()
