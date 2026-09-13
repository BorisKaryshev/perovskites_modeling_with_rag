from .interface import AgentBase
from .simple_agent import SimpleAgnet

from src.common.instance_type_enum import InstanceTypeEnum


class AgentInstanceType(InstanceTypeEnum):
    SIMPLE = ("simple", SimpleAgnet)


def create(
    name: str,
    *args,
    **kwargs,
) -> "AgentBase":
    instance_type = AgentInstanceType(name)

    result = instance_type.instance_type(*args, **kwargs)
    return result


AgentBase._set_creator(create)
