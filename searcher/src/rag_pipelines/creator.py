from .interface import RagPipeline
from .basic_rag_pipeline import BasicRagPipeline
from src.common.instance_type_enum import InstanceTypeEnum


class RagPipelineInstances(InstanceTypeEnum):
    BASIC = ("basic", BasicRagPipeline)


def create(
    name: str,
    *args,
    **kwargs,
) -> RagPipeline:
    instance_type = RagPipelineInstances(name)

    result = instance_type.instance_type(*args, **kwargs)
    return result


RagPipeline._set_creator(create)
