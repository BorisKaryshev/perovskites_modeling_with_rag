from .interface import EntryPoint

from src.agents.simple_agent import FormattingFailuresExhausted, SimpleAgnet
from src.document_parser import DocumentParser
from src.llm_providers import ChatProvider
from src.tools.perovskite_database import (
    configure_perovskite_database,
    list_registered_property_names,
    make_pdf_add_perovskite_tool,
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
            except FormattingFailuresExhausted as ex:
                logger.error(
                    "Skipping paper after 13 formatting failures: %s (%s)", pdf, ex
                )
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
        agent.add_tool(list_registered_property_names)
        agent.add_tool(make_pdf_add_perovskite_tool(str(pdf)))

        messages = [
            {
                "role": "system",
                "content": (
                    "You extract perovskite data from scientific papers into model "
                    "version 2.1 and save it with add_perovskite_structure. Use only "
                    "facts supported by the supplied paper. Pass `document` as a "
                    "native object to the tool; never serialize it into a JSON string. "
                    "The tool sets every perovskite's top-level `source` field to the "
                    "absolute path of this input PDF; omit `source` from the document. "
                    "For every identified perovskite, actively extract its reported "
                    "quantitative material properties. Inspect tables, captions, text, "
                    "and supplementary information included in the paper text. Look for "
                    "band gap/bandgap, tolerance and distortion factors, lattice "
                    "parameters and volume, transition temperatures, magnetic quantities, "
                    "conductivity, mobility, lifetime, stability, and any other measured "
                    "or calculated numeric material property. Do not leave `properties` "
                    "empty when the paper reports a numeric property for that material. "
                    "Before naming properties, call list_registered_property_names and "
                    "reuse an existing registered name whenever it describes the same "
                    "property; do not create a spelling or naming variant. Match names "
                    "by meaning, not only exact wording (for example, use existing "
                    "`band_gap` for 'band gap' or 'bandgap'). Create a new concise stable "
                    "snake_case name only when the property is genuinely distinct from "
                    "every registered name. Use that same name consistently for all "
                    "materials and measurements in this document. Give each property a "
                    "numeric value and non-empty unit exactly as reported "
                    "or a standard unit explicitly converted from the paper. Include "
                    "method and conditions (including temperature/phase when reported). "
                    "For `properties[].source`, cite the location that supports each "
                    "value when useful, such as `Table 2`, `Figure 3`, page, or section; "
                    "combine it with the PDF filename when needed to identify the source. "
                    "Do not guess a location. For each "
                    "perovskite, include a given property only once for the same value, "
                    "unit, and conditions, even when it is repeated in multiple tables, "
                    "captions, or passages; merge those citations into that one record. "
                    "Before calling the add tool, deduplicate each material's properties "
                    "by property name, value, unit, and conditions. Keep separate records "
                    "only when the reported values or meaningful conditions differ, such "
                    "as distinct phases, temperatures, or genuinely independent results. "
                    "Never invent missing "
                    "composition, structure, conditions, values, units, layers, or "
                    "citations; omit optional unknown fields. Property values must be "
                    "numbers. Put space_group in structure and textual observations in "
                    "notes instead of properties. "
                    "Each perovskite must use `formula`, never `composition`, and `ions` "
                    "must be an array. Example ion objects: "
                    "{site: 'A', compound: {name: 'guanidinium', formula: 'GUA'}, "
                    "coefficient: 1}, {site: 'B', compound: {name: 'manganese'}, "
                    "coefficient: 1}, {site: 'X', compound: {name: 'hypophosphite', "
                    "formula: 'H2POO'}, coefficient: 3}. Never put a formula string "
                    "in `ions`. "
                    "Material properties belong in perovskites; "
                    "PCE, Voc, Jsc, fill factor, EQE, and device stability belong in the "
                    "relevant layer_stack. Device performance properties should also be "
                    "extracted into layer_stacks when reported. Empty `properties` means "
                    "the paper text was checked and contains no relevant numeric property, "
                    "not merely that extraction was skipped. Create stable, unique IDs "
                    "within this document. Call the "
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
        print(await agent.run(
            messages,
            recover_formatting=True,
            required_tools=("add_perovskite_structure",),
        ))
