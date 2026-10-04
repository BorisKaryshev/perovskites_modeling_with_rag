import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import psycopg

from src.agents.simple_agent import SimpleAgnet
from src.llm_providers.interface import ToolCall
from src.tools.perovskite_database import search_perovskite_structures


class ToolLoggingTests(unittest.IsolatedAsyncioTestCase):
    async def test_connection_failure_is_logged_and_still_returned_to_model(self):
        provider = SimpleNamespace(chat=AsyncMock(side_effect=[
            SimpleNamespace(response=None, tool_calls=[ToolCall(
                name="search_perovskite_structures",
                func=search_perovskite_structures,
                arguments={"entity": "perovskite", "filters_json": '{"properties.name":"band_gap"}'},
                call_id="call_test",
            )]),
            SimpleNamespace(response="Database unavailable", tool_calls=[]),
        ]))
        with patch("src.tools.perovskite_database._database_dsn",
                   "postgresql://reader:secret-password@postgres.g:5432/perovskites"), patch(
            "src.tools.perovskite_database.psycopg.connect",
            side_effect=psycopg.OperationalError("connection refused"),
        ), self.assertLogs(level="INFO") as logs:
            result = await SimpleAgnet(provider).run([{"role": "user", "content": "Search"}])

        output = "\n".join(logs.output)
        self.assertIn("postgres.g", output)
        self.assertIn("band_gap", output)
        self.assertIn("call_test", output)
        self.assertIn("elapsed=", output)
        self.assertIn("Traceback", output)
        self.assertIn("OperationalError: connection refused", output)
        self.assertNotIn("secret-password", output)
        self.assertNotIn("PostgreSQL connected", output)
        self.assertNotIn("Tool search_perovskite_structures returned", output)
        self.assertEqual(result, "Database unavailable")
        messages = provider.chat.call_args.args[0]
        self.assertEqual(json.loads(messages[-1]["content"]),
                         {"ok": False, "error": "connection refused"})

    async def test_success_logs_duration_without_dumping_result(self):
        provider = SimpleNamespace(chat=AsyncMock(side_effect=[
            SimpleNamespace(response=None, tool_calls=[ToolCall(
                name="test_tool", func=lambda: "large private result", arguments={},
                call_id="call_success",
            )]),
            SimpleNamespace(response="Done", tool_calls=[]),
        ]))
        with self.assertLogs("src.agents.simple_agent", level="INFO") as logs:
            await SimpleAgnet(provider).run([])
        output = "\n".join(logs.output)
        self.assertIn("Starting tool test_tool", output)
        self.assertIn("Tool test_tool returned call_id=call_success elapsed=", output)
        self.assertNotIn("large private result", output)
