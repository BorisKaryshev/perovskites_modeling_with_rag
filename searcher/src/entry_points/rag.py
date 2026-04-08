from .interface import EntryPoint
from src.rag_pipelines import RagPipeline

from argparse import ArgumentParser, Namespace
import logging
from pprint import pprint as pp

logger = logging.getLogger(__name__)


class RagEntryPoint(EntryPoint):
    def __init__(self, args: Namespace):
        super().__init__(args)

        self._query = args.query
        self._config["document_store"]["options"]["limit"] = args.n_of_chunks

        self._rag = RagPipeline.create(
            self._config["rag"].pop("type"),
            config=self._config,
        )

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        parser.add_argument("query")
        parser.add_argument("-n", "--n_of_chunks", required=False, default=10, type=int)

    async def run(self) -> None:
        response = await self._rag.search(self._query, list())

        pp(response.model_dump())
