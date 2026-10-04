import unittest
from argparse import ArgumentParser
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from src.entry_points.paper_to_perovskite import PaperToPerovskiteEntryPoint


MODULE = "src.entry_points.paper_to_perovskite"


class PaperBatchTests(unittest.IsolatedAsyncioTestCase):
    def test_one_or_multiple_positional_pdfs(self):
        parser = ArgumentParser()
        PaperToPerovskiteEntryPoint.add_subparser(parser)
        self.assertEqual(parser.parse_args(["one.pdf"]).pdf, [Path("one.pdf")])
        args = parser.parse_args(["one.pdf", "two.pdf", "--max-characters", "100"])
        self.assertEqual(args.pdf, [Path("one.pdf"), Path("two.pdf")])
        self.assertEqual(args.max_characters, 100)

    async def test_papers_get_separate_agent_contexts_and_limits(self):
        entry = object.__new__(PaperToPerovskiteEntryPoint)
        entry._pdfs = [Path("one.pdf"), Path("two.pdf")]
        entry._max_characters = 5
        entry._config = {"llm_chat": {"type": "open_ai", "options": {}}}
        parser = SimpleNamespace(parse_document=AsyncMock(side_effect=["first-extra", "second-extra"]))
        agents = [Mock(run=AsyncMock(return_value="saved one")),
                  Mock(run=AsyncMock(return_value="saved two"))]
        with patch(f"{MODULE}.DocumentParser.create", return_value=parser), patch(
            f"{MODULE}.ChatProvider.create"
        ), patch(f"{MODULE}.SimpleAgnet", side_effect=agents), patch("builtins.print"):
            await entry.run()
        for agent, filename, text in zip(agents, ("one.pdf", "two.pdf"), ("first", "secon")):
            messages = agent.run.call_args.args[0]
            self.assertEqual(len(messages), 2)
            self.assertIn(filename, messages[1]["content"])
            self.assertTrue(messages[1]["content"].endswith("PAPER TEXT:\n" + text))
            agent.add_tool.assert_called_once()
        self.assertEqual([call.args[0] for call in parser.parse_document.call_args_list], entry._pdfs)

    async def test_exception_stops_remaining_papers(self):
        entry = object.__new__(PaperToPerovskiteEntryPoint)
        entry._pdfs = [Path("one.pdf"), Path("two.pdf")]
        entry._process_paper = AsyncMock(side_effect=ValueError("PDF has no text"))
        with patch("builtins.print"), self.assertLogs(MODULE, level="ERROR"), self.assertRaises(ValueError):
            await entry.run()
        entry._process_paper.assert_awaited_once_with(Path("one.pdf"))
