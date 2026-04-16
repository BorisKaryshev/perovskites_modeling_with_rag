from .interface import RagResponse, RagPipeline, VerboseRagResponse

from src.document_store import DBSchema
from src.chat_requester import ChatRequester

from pathlib import Path
from copy import deepcopy
from typing import List, Dict, Optional, Tuple
import asyncio
import logging

logger = logging.getLogger(__name__)


class NoDocsRagPipeline(RagPipeline):
    def __init__(self, config: dict, **_):
        self._config = config

        self._chat_requester = ChatRequester.create(
            self._config["chat_requester"]["type"],
            **self._config["chat_requester"]["options"],
        )
        self._chat_requester.set_output_json_schema(RagResponse.model_json_schema())

    async def add_documents(
        self,
        files: List[Path],
        n_of_parallel_added_files: int = 2,
    ):
        semaphore = asyncio.Semaphore(n_of_parallel_added_files)

        async def run(file: Path):
            async with semaphore:
                return self.add_document(file)

        asyncio.gather(*[run(i) for i in files])

    async def add_document(self, file: Path):
        logger.info(
            f"NoDocsRagPipeline was created, so ignoring adding doc with path: {file}"
        )

    async def delete_document(self, path: Path):
        logger.info(
            f"NoDocsRagPipeline was created, so ignoring deleting doc with path: {path}"
        )

    async def document_exists(self, document_path: Path) -> bool:
        return True

    async def retrieve_docs(
        self,
        query: str,
        limit: Optional[int] = None,
    ) -> List[Tuple[float, DBSchema]]:
        return []

    async def search(
        self,
        query: str,
        history: List[Dict[str, str]],
    ) -> RagResponse:
        history = deepcopy(history)

        for _ in range(3):

            response = await self._chat_requester.send_request(
                query,
                await self._store.search_by_query(query),
                history,
            )
            try:
                return RagResponse.model_validate_json(response)
            except Exception as ex:
                logger.warning(f"Failed to parse answer: {ex}")
                logger.warning(f"Got response: {response}")
                raise ex

    async def search_verbose(
        self,
        query: str,
        history: List[Dict[str, str]],
    ) -> VerboseRagResponse:
        history = deepcopy(history)

        result = VerboseRagResponse()

        for _ in range(3):
            result.generation_attempts += 1
            retrieved_docs = []
            result.chunks_retrieved = retrieved_docs

            verbose_response = await self._chat_requester.send_request_verbose(
                query,
                retrieved_docs,
                history,
            )

            result.prompt_tokens += verbose_response.prompt_tokens
            result.completion_tokens += verbose_response.completion_tokens
            result.total_tokens += verbose_response.total_tokens
            try:
                response = verbose_response.response
                result.rag_response = RagResponse.model_validate_json(response)
                return result
            except Exception as ex:
                logger.warning(f"Failed to parse answer: {ex}")
                logger.warning(f"Got response: {response}")
                raise ex
