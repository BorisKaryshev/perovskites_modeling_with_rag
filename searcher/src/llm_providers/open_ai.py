from .interface import (
    ChatProvider,
    ChatStreamResponse,
    ChatStreamResponseType,
    ChatVerboseResponse,
    EmbedderProvider,
)

import aiohttp
import json
from typing import AsyncGenerator, Dict, List
import logging

import backoff

logger = logging.getLogger(__name__)
backoff_logger = logging.getLogger(__name__ + ".backoff")

RETRY_DECO_FACTORY = lambda: backoff.on_exception(
    backoff.expo,
    (
        ConnectionError,
        TimeoutError,
    ),
    max_tries=5,
    jitter=backoff.random_jitter,
    logger=backoff_logger,
)


class OpenAIChatProvider(ChatProvider):
    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str,
        temperature: float = 0.8,
        max_completion_tokens: int = 4096,
        request_timeout: float = 90.0,
        **_,
    ):
        super().__init__()
        self._model = model
        self._base_url = base_url
        self._api_key = api_key
        self._temperature = temperature
        self._max_compeletion_tokens = max_completion_tokens

        self._request_timeout = request_timeout

    @RETRY_DECO_FACTORY()
    async def stream(
        self,
        messages: List[Dict[str, str]],
    ) -> AsyncGenerator[ChatStreamResponse, None]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": True,
            "temperature": self._temperature,
            "max_completion_tokens": self._max_compeletion_tokens,
        }
        if self._json_schema:
            payload["type"] = "json_schema"
            payload["schema"] = self._json_schema

        timeout = aiohttp.ClientTimeout(total=self._request_timeout)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.post(
                f"{self._base_url}/v1/chat/completions",
                json=payload,
            ) as response:
                if response.status != 200:
                    raise ConnectionError(
                        f"Failed to send request to OpenAI: {await response.json()}"
                    )

                while True:
                    line = (await response.content.readline()).decode().strip()
                    if not line:
                        continue
                    if not line.startswith("data"):
                        logger.warning(f"Got unexpected line: {line}")
                        continue
                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        break

                    data = json.loads(data)

                    reasoning_content = data["choices"][0]["delta"].get(
                        "reasoning_content"
                    )
                    if reasoning_content:
                        yield ChatStreamResponse(
                            data=reasoning_content,
                            content_type=ChatStreamResponseType.THINKING,
                        )

                    content = data["choices"][0]["delta"].get("content")
                    if not content:
                        continue

                    yield ChatStreamResponse(
                        data=content,
                        content_type=ChatStreamResponseType.CONTENT,
                    )

    async def chat_response_only(self, messages: List[Dict[str, str]]) -> str:
        return (await self.chat(messages)).response

    @RETRY_DECO_FACTORY()
    async def chat(self, messages: List[Dict[str, str]]) -> ChatVerboseResponse:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
        }
        if self._json_schema:
            payload["type"] = "json_schema"
            payload["json_schema"] = self._json_schema

        timeout = aiohttp.ClientTimeout(total=self._request_timeout)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.post(
                f"{self._base_url}/v1/chat/completions",
                json=payload,
            ) as response:
                if response.status != 200:
                    raise ConnectionError(
                        f"Failed to send request to OpenAI: {await response.json()}"
                    )
                output = await response.json()
                logger.info(f"Got response from llm: {output}")

                return ChatVerboseResponse(
                    response=output["choices"][0]["message"]["content"],
                    prompt_tokens=output["usage"]["prompt_tokens"],
                    completion_tokens=output["usage"]["completion_tokens"],
                    total_tokens=output["usage"]["total_tokens"],
                    thinking="",
                )


class OpenAIEmbedderProvider(EmbedderProvider):
    def __init__(self, model: str, base_url: str, api_key: str, **_):
        super().__init__()
        self._model = model
        self._base_url = base_url
        self._api_key = api_key

    @RETRY_DECO_FACTORY()
    async def embed(self, query: str) -> List[float]:
        logger.info(f"Called embed with {query = }")
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "input": query,
            "encoding_format": "float",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                f"{self._base_url}/v1/embeddings",
                json=payload,
            ) as response:
                if response.status != 200:
                    raise ConnectionError(
                        f"Failed to send embed request to OpenAI: {await response.json()}"
                    )
                output = await response.json()
                return output["data"][0]["embedding"]
