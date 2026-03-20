from .interface import (
    ChatProvider,
    ChatStreamResponse,
    ChatStreamResponseType,
    EmbedderProvider,
)

import aiohttp
import json
from typing import Dict, List, AsyncGenerator


class OllamaChatProvider(ChatProvider):
    def __init__(self, model: str, base_url: str, **_):
        super().__init__()
        self._model = model
        self._base_url = base_url

    async def stream(
        self, messages: List[Dict[str, str]]
    ) -> AsyncGenerator[ChatStreamResponse, None]:
        headers = {
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": True,
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                f"{self._base_url}/api/chat",
                json=payload,
            ) as response:
                if response.status != 200:
                    raise ConnectionError(
                        f"Failed to send request to Ollama: {await response.json()}"
                    )

                while True:
                    line = (await response.content.readline()).decode()
                    if not line:
                        break
                    data = json.loads(line)
                    if data["done"]:
                        break

                    thinking = data["message"].get("thinking")
                    if thinking:
                        yield ChatStreamResponse(
                            data=thinking, content_type=ChatStreamResponseType.THINKING
                        )
                    content = data["message"].get("content")
                    if not content:
                        continue

                    yield ChatStreamResponse(
                        data=content, content_type=ChatStreamResponseType.CONTENT
                    )

    async def chat_response_only(self, messages: List[Dict[str, str]]) -> str:
        return (await self.chat(messages)).get("message", {}).get("content", "")

    async def chat(self, messages: List[Dict[str, str]]) -> dict:
        payload = {"model": self._model, "messages": messages, "stream": False}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self._base_url}/api/chat",
                json=payload,
            ) as response:
                if response.status != 200:
                    raise ConnectionError(
                        f"Failed to send request to ollama: {await response.json()}"
                    )
                output = await response.json()
                if output["model"] != self._model:
                    raise RuntimeError(
                        f"Ollama returned answer from different model. Expected: {self._model}, got: {output['model']}"
                    )
                return output


class OllamaEmbedderProvider(EmbedderProvider):
    def __init__(self, model: str, base_url: str, **_):
        super().__init__()
        self._model = model
        self._base_url = base_url

    async def embed(self, query: str) -> List[float]:
        payload = {"model": self._model, "input": query}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self._base_url}/api/embed",
                json=payload,
            ) as response:
                if response.status != 200:
                    raise ConnectionError(
                        f"Failed to send embed request to ollama: {await response.json()}"
                    )
                output = await response.json()
                if output["model"] != self._model:
                    raise RuntimeError(
                        f"Ollama returned answer from different model. Expected: {self._model}, got: {output['model']}"
                    )
                return output["embeddings"][0]
