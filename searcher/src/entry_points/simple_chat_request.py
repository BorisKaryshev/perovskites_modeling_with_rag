from .interface import EntryPoint

from src.llm_providers import ChatProvider, ChatStreamResponseType


from argparse import ArgumentParser, Namespace
import time
import logging

from termcolor import colored

logger = logging.getLogger(__name__)


class SimpleChatRequestEntryPoint(EntryPoint):
    def __init__(self, args: Namespace):
        super().__init__(args)

        self._query = args.query

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        parser.add_argument("query", type=str)

    async def run(self) -> None:
        logger.debug("entery_point started")

        chat_provider = ChatProvider.create(
            self._config["llm_chat"]["type"],
            **self._config["llm_chat"]["options"],
        )

        messages = [
            {
                "role": "system",
                "content": "Your task is to generate short answer on user query",
            },
            {"role": "user", "content": self._query},
        ]

        begin = time.time()

        mode = ChatStreamResponseType.THINKING

        async for i in chat_provider.stream(messages):
            if i.content_type is not mode:
                mode = ChatStreamResponseType.CONTENT
                print()

            if i.content_type is ChatStreamResponseType.THINKING:
                print(colored(i.data, "dark_grey", "on_black"), end="")
            if i.content_type is ChatStreamResponseType.CONTENT:
                print(colored(i.data, "white", "on_black"), end="")

        print()

        end = time.time()
        logger.info(f"Query took: {int((end - begin) * 1000)} ms")
