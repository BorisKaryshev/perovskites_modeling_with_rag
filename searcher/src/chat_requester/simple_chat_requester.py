from .interface import ChatRequester
from src.document_store import DBSchema
from src.llm_providers import ChatProvider, ChatStreamResponse, ChatVerboseResponse
from src.rag_pipelines.interface import RagResponse

from typing import AsyncGenerator, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

RECORD_FORMAT = """
BEGINGING OF CHUNK RECORD
Record retrieved from database with score: {score}
CHUNK:
{record}

From file: {filename}
Chunk idx: {chunk_idx}
END OF CHUNK RECORD
"""

DEFAULT_PROMPT = """
You are intellegent agent for searching information in text.
Your task is to retrieve answer from given chunks of documents.

OUTPUT FORMAT IN PYDANTIC NOTATION:
{output_format}
ANSWER IN JSON WHICH SATISFIES PROVIDED FORMAT!!!

EXAMPLE OF OUTPUT:
{output_example}

If provided chunks do not contain answer, print: provided documents do not contain answer.
Provide references (file names) of chunks you found answer in.

USER QUERY: {query}

DOCUMENT CHUNKS:
{records}
"""


def _read_file(file_path: str) -> str:
    with open(file_path, mode="r") as f:
        return f.read()


class SimpleChatRequester(ChatRequester):
    def __init__(
        self,
        chat_provider_type: str,
        path_to_prompt: Optional[str] = None,
        **kwargs,
    ):
        super().__init__()
        self._path_to_prompt = path_to_prompt
        self._chat_provider = ChatProvider.create(chat_provider_type, **kwargs)

        self._prompt: Optional[str] = None

        self._output_example_string = "\n".join(
            i.model_dump_json() for i in RagResponse.filled_response_examples()
        )

    async def lazy_load(self) -> None:
        if self._prompt is not None:
            return
        if self._path_to_prompt is not None:
            self._prompt = await self.apply(_read_file, self._path_to_prompt)
        else:
            self._prompt = DEFAULT_PROMPT

    async def _prepare_request(
        self,
        query: str,
        records_with_scores: List[Tuple[float, DBSchema]],
        history: List[Dict[str, str]],
    ):
        await self.lazy_load()

        if self._prompt is None:
            return

        records_prompt = ""
        for score, record in records_with_scores:
            records_prompt += RECORD_FORMAT.format(
                record=record.payload,
                score=score,
                filename=record.doc_path,
                chunk_idx=record.chunk_idx,
            )

        prompt = self._prompt.format(
            query=query,
            records=records_prompt,
            output_format=str(self._json_schema),
            output_example=self._output_example_string,
        )
        history += [
            {"role": "system", "content": prompt},
        ]

    async def send_request_stream(
        self,
        query: str,
        records_with_scores: List[Tuple[float, DBSchema]],
        history: List[Dict[str, str]],
    ) -> AsyncGenerator[ChatStreamResponse, None]:
        await self._prepare_request(query, records_with_scores, history)

        async for i in self._chat_provider.stream(history):
            yield i

    async def send_request(
        self,
        query: str,
        records_with_scores: List[Tuple[float, DBSchema]],
        history: List[Dict[str, str]],
    ) -> str:
        return (
            await self.send_request_verbose(query, records_with_scores, history)
        ).response

    async def send_request_verbose(
        self,
        query: str,
        records_with_scores: List[Tuple[float, DBSchema]],
        history: List[Dict[str, str]],
    ) -> ChatVerboseResponse:
        await self._prepare_request(query, records_with_scores, history)
        return await self._chat_provider.chat(history)
