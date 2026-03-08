from .interface import DocumentChunker
from .langchain_chunker import LangchainChunker
from src.common.instance_type_enum import InstanceTypeEnum


class DocumentChunkerInstances(InstanceTypeEnum):
    LANGCHAIN_CHUNKER = ("langchain", LangchainChunker)


def create(
    name: str,
    *args,
    **kwargs,
) -> "DocumentChunker":
    instance_type = DocumentChunkerInstances(name)

    result = instance_type.instance_type(*args, **kwargs)
    return result


DocumentChunker._set_creator(create)
