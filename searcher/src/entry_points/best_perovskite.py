from .interface import EntryPoint

from src.agents.simple_agent import SimpleAgnet
from src.llm_providers import ChatProvider
from src.tools.perovskite_database import (
    LAYER_STACK_SEARCH_FIELDS,
    PEROVSKITE_SEARCH_FIELDS,
    configure_perovskite_database,
    search_perovskite_structures,
)

from argparse import ArgumentParser, Namespace
import os


class BestPerovskiteEntryPoint(EntryPoint):
    """Example agent: search and compare stored perovskites for a user query."""

    def __init__(self, args: Namespace):
        super().__init__(args)
        self._query = args.query

        database_config = self._config.get("perovskite_database", {})
        dsn = os.environ.get("DATABASE_URL") or database_config.get("dsn")
        if dsn:
            configure_perovskite_database(str(dsn))

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        parser.add_argument("query", help="Natural-language selection criteria")

    async def run(self) -> None:
        chat_provider = ChatProvider.create(
            self._config["llm_chat"]["type"],
            **self._config["llm_chat"]["options"],
        )
        agent = SimpleAgnet(chat_provider=chat_provider)
        agent.add_tool(search_perovskite_structures)

        messages = [
            {
                "role": "system",
                "content": (
                    "You select the best perovskite from the PostgreSQL database for "
                    "the user's criteria. You must search before answering. Search values "
                    "are case-insensitive PostgreSQL regular expressions and fields in a "
                    "single call are AND-combined. Regex search does not perform numeric "
                    "range comparisons: search broadly by property name/unit, inspect "
                    "returned numeric values, and compare them yourself. Device metrics "
                    "are on layer_stack records; search those first when the query concerns "
                    "PCE, Voc, Jsc, fill factor, EQE, architecture, layers, or device "
                    "stability. Then search referenced perovskite IDs when composition or "
                    "material details are needed. Make more than one tool call when useful. "
                    "Do not claim that missing data means a property is zero or absent. "
                    "State the ranking criterion, cite dataset_id and material id, compare "
                    "the strongest candidates, and say when evidence is insufficient.\n\n"
                    "Perovskite search fields: "
                    + ", ".join(PEROVSKITE_SEARCH_FIELDS)
                    + ".\nLayer-stack search fields: "
                    + ", ".join(LAYER_STACK_SEARCH_FIELDS)
                    + "."
                ),
            },
            {"role": "user", "content": self._query},
        ]
        print(await agent.run(messages))
