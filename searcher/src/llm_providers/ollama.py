from typing import Dict, List

from .interface import ChatProvider, EmbedderProvider

import aiohttp


class OllamaChatProvider(ChatProvider):
    def __init__(self, model: str, base_url: str, **_):
        super().__init__()
        self._model = model
        self._base_url = base_url

    async def chat_response_only(self, messages: List[Dict[str, str]]) -> str:
        return (await self.chat(messages)).get("message", {}).get("content", "")

    async def chat(self, messages: List[Dict[str, str]]) -> dict:
        payload = {"model": self._model, "messages": messages}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self._base_url}/api/chat",
                json=payload,
            ) as response:
                if response.status != 200:
                    raise ConnectionError("Failed to send request to ollama")
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
                    raise ConnectionError("Failed to send embed request to ollama")
                output = await response.json()
                if output["model"] != self._model:
                    raise RuntimeError(
                        f"Ollama returned answer from different model. Expected: {self._model}, got: {output['model']}"
                    )
                return output["embeddings"][0]
