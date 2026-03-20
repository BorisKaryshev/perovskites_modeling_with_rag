from src.common.instance_type_enum import InstanceTypeEnum
from .interface import QDrantVectoriser
from .PlainQdrantVectorizer import PlainQdrantVectorizer
from .PlainHybridVectorizer import PlainHybridQdrantVectorizer


class QDrantVectorizerInstances(InstanceTypeEnum):
    PLAIN = ("plain", PlainQdrantVectorizer)
    PLAIN_HYBRID = ("plain_hybrid", PlainHybridQdrantVectorizer)


def create_qdrant_vectorizer(
    name: str,
    *args,
    **kwargs,
) -> QDrantVectoriser:
    instance_type = QDrantVectorizerInstances(name)
    result = instance_type.instance_type(*args, **kwargs)
    return result


QDrantVectoriser._set_creator(create_qdrant_vectorizer)
