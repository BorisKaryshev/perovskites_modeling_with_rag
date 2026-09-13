from .interface import EntryPoint

from src.agents.simple_agent import SimpleAgnet
from src.llm_providers import ChatProvider
from src.tools import tool

from argparse import ArgumentParser, Namespace
import time
import logging

logger = logging.getLogger(__name__)


@tool
def get_current_time() -> str:
    """
    This function returns current time in format: YYYY:MM:DD HH:MM:SS
    """

    return "2025:03:04 13:04:53"


@tool
def summator(a: float, b: float) -> float:
    """
    returns: a + b
    """

    return a + b


@tool
def multiplicator(a: float, b: float) -> float:
    """
    returns: a * b
    """

    return a * b


@tool
def expo(a: float, b: float) -> float:
    """
    returns: a ^ b

    b can be any float in range (-inf:+inf)
    including negatives or (0;1]
    You can use it to compute not only positive powers, but roots as well
    It supports fractional components
    """

    return a**b


class SimpleAgentWorking(EntryPoint):
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

        agent = SimpleAgnet(chat_provider=chat_provider)
        agent.add_tool(get_current_time)
        agent.add_tool(summator)
        agent.add_tool(multiplicator)
        agent.add_tool(expo)

        messages = [
            {
                "role": "system",
                "content": "Your task is to generate short answer on user query. Use tools. Do not try to pass args in tools like 'result_of_other_tool_call' - they do not support this!. You can use tools sequentially. Not all in one request.",
            },
            {"role": "user", "content": self._query},
        ]

        begin = time.time()

        response = await agent.run(messages)
        print(response)

        end = time.time()
        logger.info(f"Query took: {int((end - begin) * 1000)} ms")
