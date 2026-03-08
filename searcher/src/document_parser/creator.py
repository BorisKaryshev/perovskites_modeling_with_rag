from src.common.instance_type_enum import InstanceTypeEnum
from .interface import DocumentParser
from .markdown_parser import MarkdownParser
from .auto_parser import AutoParser


class DocumentParserInstances(InstanceTypeEnum):
    DEFAULT = ("default", MarkdownParser)
    AUTO = ("auto", AutoParser)
    MARKDOWN = ("markdown", MarkdownParser)


def create(
    name: str,
    *args,
    **kwargs,
) -> "DocumentParser":
    instance_type = DocumentParserInstances(name)

    result = instance_type.instance_type(*args, **kwargs)
    return result


DocumentParser._set_creator(create)
