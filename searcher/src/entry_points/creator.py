from .interface import EntryPoint
from .example_entry_point import ExampleEntryPoint
from src.common.instance_type_enum import InstanceTypeEnum

from argparse import ArgumentParser, Namespace


class EnteryPointInstances(InstanceTypeEnum):
    EXAMPLE = ("example", ExampleEntryPoint)


def parse_arguments() -> Namespace:
    parser = ArgumentParser()
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
