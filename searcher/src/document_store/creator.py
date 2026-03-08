from src.common.instance_type_enum import InstanceTypeEnum
from .interface import DocumentStore
from .QDrantDBStore import QDrantDBStore, QDrantVectoriser
from .PlainQdrantVectorizer import PlainQdrantVectorizer


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


class QDrantVectorizerInstances(InstanceTypeEnum):
    PLAIN = ("plain", PlainQdrantVectorizer)


def create_qdrant_vectorizer(
    name: str,
    *args,
    **kwargs,
) -> QDrantVectoriser:
    instance_type = QDrantVectorizerInstances(name)
    result = instance_type.instance_type(*args, **kwargs)
    return result


QDrantVectoriser._set_creator(create_qdrant_vectorizer)
