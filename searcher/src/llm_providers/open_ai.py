from .interface import (
    ChatProvider,
    ChatStreamResponse,
    ChatStreamResponseType,
    EmbedderProvider,
)

import aiohttp
import json
from typing import AsyncGenerator, Dict, List
import logging

logger = logging.getLogger(__name__)


class OpenAIChatProvider(ChatProvider):
    def __init__(
        self, model: str, base_url: str, api_key: str, temperature: float = 0.8, **_
    ):
        super().__init__()
        self._model = model
        self._base_url = base_url
        self._api_key = api_key
        self._temperature = temperature

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
        }
        if self._json_schema:
            payload["type"] = "json_schema"
            payload["schema"] = self._json_schema

        async with aiohttp.ClientSession(headers=headers) as session:
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
        output = ""
        async for i in self.stream(messages):
            if i.content_type == ChatStreamResponseType.CONTENT:
                output += i.data
        return output

        return (await self.chat(messages)).get("message", {}).get("content", "")

    async def chat(self, messages: List[Dict[str, str]]) -> dict:
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

        async with aiohttp.ClientSession(headers=headers) as session:
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
                return output


class OpenAIEmbedderProvider(EmbedderProvider):
    def __init__(self, model: str, base_url: str, api_key: str, **_):
        super().__init__()
        self._model = model
        self._base_url = base_url
        self._api_key = api_key

    async def embed(self, query: str) -> List[float]:
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
