from .interface import QDrantVectoriser
from src.llm_providers import EmbedderProvider

from qdrant_client import models

import logging

logger = logging.getLogger(__name__)


class PlainQdrantVectorizer(QDrantVectoriser):
    def __init__(self, provider_type: str, base_url: str, model: str, *_, **kwargs):
        super().__init__()
        logger.debug(f"Creating embedder with opts: {kwargs}")
        self._client = EmbedderProvider.create(
            name=provider_type,
            base_url=base_url,
            model=model,
            **kwargs,
        )
        self._embedding_size = None
        logger.info("Created PlainQdrantVectorizer")

    async def vectorize_for_upsert(self, data: str) -> dict:
        logger.debug("Calling vectorize_for_upsert")
        return {"dense": await self._client.embed(data)}

    async def vectorize_for_search(self, data: str) -> dict:
        return {
            "using": "dense",
            "query": await self._client.embed(data),
        }

    async def create_collection_config(self) -> dict:
        if self._embedding_size is None:
            self._embedding_size = len(await self._client.embed("sample text"))

        return {
            "vectors_config": {
                "dense": models.VectorParams(
                    distance=models.Distance.COSINE,
                    size=self._embedding_size,
                )
            }
        }
