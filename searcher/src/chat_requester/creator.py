from .interface import ChatRequester
from .simple_chat_requester import SimpleChatRequester
from src.common.instance_type_enum import InstanceTypeEnum


class ChatRequesterInstances(InstanceTypeEnum):
    SIMPLE = ("simple", SimpleChatRequester)


def create(
    name: str,
    *args,
    **kwargs,
) -> "ChatRequester":
    instance_type = ChatRequesterInstances(name)

    result = instance_type.instance_type(*args, **kwargs)
    return result


ChatRequester._set_creator(create)
