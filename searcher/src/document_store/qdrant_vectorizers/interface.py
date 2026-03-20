from src.common.class_with_creator import ClassWithCreator

from abc import ABC, abstractmethod


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
