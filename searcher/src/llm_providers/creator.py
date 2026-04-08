from .interface import ChatProvider, EmbedderProvider
from .open_ai import OpenAIChatProvider, OpenAIEmbedderProvider
from src.common.instance_type_enum import InstanceTypeEnum


class ChatProviderInstances(InstanceTypeEnum):
    OPEN_AI = ("open_ai", OpenAIChatProvider)


class EmbedderProviderInstances(InstanceTypeEnum):
    OPEN_AI = ("open_ai", OpenAIEmbedderProvider)


def create_chat_provider(
    name: str,
    *args,
    **kwargs,
) -> "ChatProvider":
    instance_type = ChatProviderInstances(name)

    result = instance_type.instance_type(*args, **kwargs)
    return result


def create_embedding_provider(
    name: str,
    *args,
    **kwargs,
) -> "EmbedderProvider":
    instance_type = EmbedderProviderInstances(name)

    result = instance_type.instance_type(*args, **kwargs)
    return result


ChatProvider._set_creator(create_chat_provider)
EmbedderProvider._set_creator(create_embedding_provider)
