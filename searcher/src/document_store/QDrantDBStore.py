from src.common.class_with_creator import ClassWithCreator
from .interface import DBSchema, DocumentMustBeDeletedFilter, DocumentStore

import asyncio
from typing import List, Tuple
from abc import ABC, abstractmethod
from itertools import batched
import logging

from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct

logger = logging.getLogger(__name__)


class QDrantVectoriser(ABC, ClassWithCreator):

    @abstractmethod
    async def vectorize_for_upsert(self, data: str) -> dict:
        pass

    @abstractmethod
    async def vectorize_for_search(self, data: str) -> dict:
        pass

    @abstractmethod
    async def create_collection_config(self) -> dict:
        pass

    @staticmethod
    def create(
        instance_name: str,
        *args,
        **kwargs,
    ) -> "QDrantVectoriser":
        return QDrantVectoriser._create(instance_name, *args, **kwargs)


class QDrantDBStore(DocumentStore):
    def __init__(
        self,
        collection_name: str,
        vectorizer: dict,
        n_of_pointis_limit: int = 10,
        force_recreate_collection: bool = False,
        **kwargs,
    ):
        super().__init__()

        self._client = AsyncQdrantClient(**kwargs)
        self._collection_name = collection_name
        self._n_of_pointis_limit = n_of_pointis_limit
        self._force_recreate_collection = force_recreate_collection
        vectorizer_type = vectorizer.pop("vectorizer_type")
        self._vectorizer = QDrantVectoriser.create(
            vectorizer_type,
            **vectorizer,
        )

        self._collection_creator_was_called = False
        self._collection_creator_lock = asyncio.Lock()

    async def try_create_collection(self):
        async with self._collection_creator_lock:
            if self._collection_creator_was_called:
                return

            collection_exists = await self._client.collection_exists(
                self._collection_name
            )

            if self._force_recreate_collection:
                collection_exists = await self._client.delete_collection(
                    self._collection_name
                )

            if not collection_exists or self._force_recreate_collection:
                logger.info("Creating collection in qdrant")
                config = await self._vectorizer.create_collection_config()

                collection_exists = await self._client.create_collection(
                    collection_name=self._collection_name,
                    **config,
                )
            self._collection_creator_was_called = True

    async def add_record(self, record: DBSchema) -> None:
        await self.try_create_collection()

        logger.debug(f"Adding record to store: {record =}")
        vector = await self._vectorizer.vectorize_for_upsert(record.key)
        await self._client.upsert(
            collection_name=self._collection_name,
            points=[
                PointStruct(vector=vector, payload=record.model_dump(), id=record.id)
            ],
        )

    async def search_by_query(self, query: str) -> List[Tuple[float, DBSchema]]:
        await self.try_create_collection()

        logger.info(f"Searching by query: '{query}'")
        search_vectors = await self._vectorizer.vectorize_for_search(query)

        response = await self._client.query_points(
            collection_name=self._collection_name,
            limit=self._n_of_pointis_limit,
            **search_vectors,
        )
        response = response.points

        result = [(i.score, DBSchema.model_validate(i.payload)) for i in response]
        return result

    async def delete_document(self, delete_filter: DocumentMustBeDeletedFilter):
        await self.try_create_collection()

        qdrant_filter = await delete_filter.create_filter_for_qdrant()
        if qdrant_filter is not None:
            await self._client.delete(
                collection_name=self._collection_name,
                points_selector=qdrant_filter,
            )
            return

        offset = None
        ids_to_delete = []
        while True:
            batch, offset = await self._client.scroll(
                self._collection_name,
                with_payload=True,
                with_vectors=False,
                offset=offset,
                limit=self._n_of_pointis_limit,
            )
            if not batch:
                break

            for i in batch:
                record = DBSchema.model_validate(i.payload)
                if not delete_filter(record):
                    continue

                ids_to_delete.append(record.id)

        if not ids_to_delete:
            return

        async with asyncio.TaskGroup() as task_group:
            for batch in batched(ids_to_delete, self._n_of_pointis_limit):
                task_group.create_task(
                    self._client.delete(
                        collection_name=self._collection_name,
                        points_selector=list(batch),
                    )
                )
