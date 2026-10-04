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
import logging
import os
from pathlib import Path


logger = logging.getLogger(__name__)


class PaperToPerovskiteEntryPoint(EntryPoint):
    """Extract model v2.1 records from one or more PDFs, one paper at a time."""

    def __init__(self, args: Namespace):
        super().__init__(args)
        self._pdfs = [pdf.expanduser().resolve() for pdf in args.pdf]
        self._max_characters = args.max_characters

        for pdf in self._pdfs:
            if not pdf.is_file():
                raise FileNotFoundError(f"PDF not found: {pdf}")
            if pdf.suffix.casefold() != ".pdf":
                raise ValueError(f"Expected a .pdf file, got: {pdf}")

        database_config = self._config.get("perovskite_database", {})
        dsn = os.environ.get("DATABASE_URL") or database_config.get("dsn")
        if dsn:
            configure_perovskite_database(str(dsn))

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        parser.add_argument("pdf", type=Path, nargs="+", help="One or more scientific papers in PDF format")
        parser.add_argument(
            "--max-characters",
            type=int,
            default=120_000,
            help="Maximum extracted characters per paper sent to the model (default: 120000)",
        )

    async def run(self) -> None:
        for index, pdf in enumerate(self._pdfs, start=1):
            logger.info("Processing paper %d/%d: %s", index, len(self._pdfs), pdf)
            print(f"Paper {index}/{len(self._pdfs)}: {pdf}", flush=True)
            try:
                await self._process_paper(pdf)
            except Exception:
                logger.exception("Paper processing failed: %s; stopping batch", pdf)
                raise

    async def _process_paper(self, pdf: Path) -> None:
        parser = DocumentParser.create("auto")
        paper_text = await parser.parse_document(pdf)
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

        messages = [
            {
                "role": "system",
                "content": (
                    "You extract perovskite data from scientific papers into model "
                    "version 2.1 and save it with add_perovskite_structure. Use only "
                    "facts supported by the supplied paper. Pass `document` as a "
                    "native object to the tool; never serialize it into a JSON string. "
                    "Never invent missing "
                    "composition, structure, conditions, values, units, layers, or "
                    "citations; omit optional unknown fields. Property values must be "
                    "numbers and property units must be non-empty. Put space_group in "
                    "structure and textual observations in notes instead of properties. "
                    "Keep repeated measurements as separate properties. Material "
                    "properties belong in perovskites; "
                    "PCE, Voc, Jsc, fill factor, EQE, and device stability belong in the "
                    "relevant layer_stack. Empty lists mean only that no records were "
                    "extracted. Create stable, unique IDs within this document. Call the "
                    "add tool exactly once after checking the object against its tool schema."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Extract and store the perovskite data reported in {pdf.name}. "
                    "After the tool succeeds, summarize the inserted dataset ID and any "
                    "important limitations in the extraction.\n\nPAPER TEXT:\n"
                    + paper_text
                ),
            },
        ]
        print(await agent.run(messages))
