from src.common.document_type import DocumentType
from .interface import DocumentParser

from pathlib import Path
import logging

from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PdfParser(DocumentParser):
    def __init__(self):
        super().__init__()
        logger.info("Creating PdfParser")

    @staticmethod
    def _parse_document_impl(document_path: str) -> str:
        reader = PdfReader(document_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    async def parse_document(self, document_path: Path) -> str:
        logger.info(f"Called pdf parser with path: {document_path}")
        return await self.apply(self._parse_document_impl, str(document_path))
