from .interface import EntryPoint
from src.common.instance_type_enum import InstanceTypeEnum

from .example_entry_point import ExampleEntryPoint
from .add_document import AddDocumentEntryPoint
from .simple_search import SimpleSearchEntryPoint
from .remove_file import RemoveFilesEntryPoint
from .gradio_interface import GradioEntryPoint
from .simple_chat_request import SimpleChatRequestEntryPoint
from .eval import EvalEntryPoint

from argparse import ArgumentParser, Namespace


class EnteryPointInstances(InstanceTypeEnum):
    EXAMPLE = ("example", ExampleEntryPoint)
    ADD_DOCUMENT = ("add_file", AddDocumentEntryPoint)
    SIMPLE_SEARCH = ("simple_search", SimpleSearchEntryPoint)
    REMOVE_FILES = ("remove_files", RemoveFilesEntryPoint)
    GRADIO = ("gradio", GradioEntryPoint)
    SIMPLE_CHAT_REQUEST = ("simple_chat_request", SimpleChatRequestEntryPoint)
    EVAL = ("eval", EvalEntryPoint)


def parse_arguments() -> Namespace:
    parser = ArgumentParser()
    EntryPoint.add_subparser(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for i in EnteryPointInstances:
        class_subparser = subparsers.add_parser(i.value)
        current_type: EntryPoint = i.instance_type

        current_type.add_subparser(class_subparser)

    return parser.parse_args()


def create() -> "ExampleEntryPoint":
    args = parse_arguments()
    instance_type = EnteryPointInstances(args.command)

    result = instance_type.instance_type(args)
    return result


EntryPoint._set_creator(create)
