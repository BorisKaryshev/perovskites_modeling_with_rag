from .interface import EntryPoint

from src.agents.simple_agent import SimpleAgnet
from src.document_parser import DocumentParser
from src.llm_providers import ChatProvider
from src.tools.perovskite_database import (
    add_perovskite_structure,
    configure_perovskite_database,
    get_perovskite_model_schema,
)

from argparse import ArgumentParser, Namespace
import json
import logging
import os
from pathlib import Path


logger = logging.getLogger(__name__)


class PaperToPerovskiteEntryPoint(EntryPoint):
    """Example agent: extract model v2.1 records from a PDF and store them."""

    def __init__(self, args: Namespace):
        super().__init__(args)
        self._pdf = args.pdf.expanduser().resolve()
        self._max_characters = args.max_characters

        if not self._pdf.is_file():
            raise FileNotFoundError(f"PDF not found: {self._pdf}")
        if self._pdf.suffix.casefold() != ".pdf":
            raise ValueError(f"Expected a .pdf file, got: {self._pdf}")

        database_config = self._config.get("perovskite_database", {})
        dsn = os.environ.get("DATABASE_URL") or database_config.get("dsn")
        if dsn:
            configure_perovskite_database(str(dsn))

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        parser.add_argument("pdf", type=Path, help="Scientific paper in PDF format")
        parser.add_argument(
            "--max-characters",
            type=int,
            default=120_000,
            help="Maximum extracted characters sent to the model (default: 120000)",
        )

    async def run(self) -> None:
        parser = DocumentParser.create("auto")
        paper_text = await parser.parse_document(self._pdf)
        if not paper_text.strip():
            raise ValueError(
                "No text could be extracted from the PDF; OCR may be required"
            )
        if len(paper_text) > self._max_characters:
            logger.warning(
                "PDF text contains %d characters; truncating to %d",
                len(paper_text),
                self._max_characters,
            )
            paper_text = paper_text[: self._max_characters]

        chat_provider = ChatProvider.create(
            self._config["llm_chat"]["type"],
            **self._config["llm_chat"]["options"],
        )
        agent = SimpleAgnet(chat_provider=chat_provider)
        agent.add_tool(add_perovskite_structure)

        schema = json.dumps(
            get_perovskite_model_schema(), ensure_ascii=False, separators=(",", ":")
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You extract perovskite data from scientific papers into model "
                    "version 2.1 and save it with add_perovskite_structure. Use only "
                    "facts supported by the supplied paper. Never invent missing "
                    "composition, structure, conditions, values, units, layers, or "
                    "citations; omit optional unknown fields. Keep repeated measurements "
                    "as separate properties. Material properties belong in perovskites; "
                    "PCE, Voc, Jsc, fill factor, EQE, and device stability belong in the "
                    "relevant layer_stack. Empty lists mean only that no records were "
                    "extracted. Create stable, unique IDs within this document. Call the "
                    "add tool exactly once after checking the JSON against this schema: "
                    + schema
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Extract and store the perovskite data reported in {self._pdf.name}. "
                    "After the tool succeeds, summarize the inserted dataset ID and any "
                    "important limitations in the extraction.\n\nPAPER TEXT:\n"
                    + paper_text
                ),
            },
        ]
        print(await agent.run(messages))
