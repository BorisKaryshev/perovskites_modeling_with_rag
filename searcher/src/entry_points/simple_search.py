from .interface import EntryPoint

from src.document_store import DocumentStore

from argparse import ArgumentParser, Namespace
import json
import time
import logging

logger = logging.getLogger(__name__)


class SimpleSearchEntryPoint(EntryPoint):
    def __init__(self, args: Namespace):
        super().__init__(args)

        self._query = args.query
        self._limit = args.limit
        self._json = args.json

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        parser.add_argument("-l", "--limit", default=5, type=int, required=False)
        parser.add_argument(
            "-j",
            "--json",
            default=False,
            action="store_true",
        )
        parser.add_argument("query", type=str)

    async def run(self) -> None:
        logger.debug("entery_point started")
        store = DocumentStore.create(
            self._config["document_store"]["type"],
            limit=self._limit,
            **self._config["document_store"]["options"],
        )

        begin = time.time()

        for score, record in await store.search_by_query(self._query):
            if not self._json:
                print(score)
                print(record.payload)
                print("-" * 20)
            else:
                d = {"score": score, **json.loads(record.model_dump_json())}
                print(json.dumps(d))

        end = time.time()
        logger.info(f"Search took: {int((end - begin) * 1000)} ms")
