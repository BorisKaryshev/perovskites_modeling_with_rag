from src.common.class_with_creator import ClassWithCreator
from src.common.utils import setup_default_logger

from abc import ABC, abstractmethod
from argparse import ArgumentParser


class EntryPoint(ABC, ClassWithCreator):
    def __init__(self):
        setup_default_logger()

    @abstractmethod
    async def run(self) -> None:
        pass

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        pass

    @staticmethod
    def create() -> "EntryPoint":
        return EntryPoint._create()
