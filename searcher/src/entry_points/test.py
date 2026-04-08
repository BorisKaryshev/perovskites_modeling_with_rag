from .interface import EntryPoint


from argparse import ArgumentParser, Namespace
import logging
from pathlib import Path

from git import Repo, Git, index

logger = logging.getLogger(__name__)


class TestEntryPoint(EntryPoint):
    def __init__(self, args: Namespace):
        super().__init__(args)

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        pass

    async def run(self) -> None:
        logger.info(f"Running file: {__file__}")

        working_dir = Path(__file__)
        logger.info(f"Got working dir: {working_dir}")

        git_repo = Repo(working_dir, search_parent_directories=True)

        logger.info(f"{git_repo.is_dirty() = }")
