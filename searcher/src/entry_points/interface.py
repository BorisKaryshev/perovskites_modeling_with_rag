from src.common.class_with_creator import ClassWithCreator
from src.common.utils import setup_default_logger, parse_config, setup_logger

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from pathlib import Path


class EntryPoint(ABC, ClassWithCreator):
    def __init__(self, args: Namespace):
        setup_default_logger()
        self._config = parse_config(args.config)
        setup_logger(self._config.get("logging"))

    @abstractmethod
    async def run(self) -> None:
        pass

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "-c",
            "--config",
            required=True,
            help="File with configuration for services",
            type=Path,
        )

    @staticmethod
    def create() -> "EntryPoint":
        return EntryPoint._create()
