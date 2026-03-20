from src.common.instance_type_enum import InstanceTypeEnum
from .interface import DocumentStore
from .QDrantDBStore import QDrantDBStore


class DocumentStoreInstances(InstanceTypeEnum):
    QDRANT = ("qdrant", QDrantDBStore)


def create_document_store(
    name: str,
    *args,
    **kwargs,
) -> DocumentStore:
    instance_type = DocumentStoreInstances(name)
    result = instance_type.instance_type(*args, **kwargs)
    return result


DocumentStore._set_creator(create_document_store)
