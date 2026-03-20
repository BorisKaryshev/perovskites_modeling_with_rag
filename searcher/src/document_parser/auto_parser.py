from .interface import DocumentParser
from .markdown_parser import MarkdownParser
from .pdf_parser import PdfParser
from src.common.document_type import DocumentType

from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AutoParser(DocumentParser):
    def __init__(self):
        super().__init__()
        logger.info("Creating AutoParser")

        self.__sub_parsers = {
            DocumentType.MARKDOWN: MarkdownParser(),
            DocumentType.PDF: PdfParser(),
        }

    async def parse_document(self, document_path: Path) -> str:
        logger.info(f"Running document parsing for: {document_path}")
        doc_type = await self.get_doc_type(document_path)
        parser = self.__sub_parsers.get(doc_type)

        if parser is None:
            raise ValueError("Got unsupported file format")

        return await parser.parse_document(document_path)
