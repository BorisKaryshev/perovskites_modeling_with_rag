from src.common.document_type import DocumentType
from .interface import DocumentParser

from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MarkdownParser(DocumentParser):
    def __init__(self):
        super().__init__()
        logger.info("Creating MarkdownParser")

    @staticmethod
    def _parse_document_impl(document_path: str) -> str:
        with open(document_path) as f:
            return f.read()

    async def parse_document(self, document_path: Path) -> str:
        logger.info(f"Called markdown parser with path: {document_path}")
        return await self.apply(self._parse_document_impl, str(document_path))
