from document_store import DocumentStore, DBSchema
from document_parser import DocumentParser
from document_chunker import DocumentChunker

from pathlib import Path


class PrevosciteRetriever:
    def __init__(
        self,
        document_store: DocumentStore,
        document_parser: DocumentParser,
        document_chunker: DocumentChunker,
    ):
        self.__document_store = document_store
        self.__document_parser = document_parser
        self.__document_chunker = document_chunker

    async def add_document(self, document_path: Path):
        document_path = document_path.resolve()
        text = await self.__document_parser.parse_document(document_path)
        chunks = await self.__document_chunker.chunk_document(text)

        creation_datetime = await self.__document_parser.get_doc_creation_date(
            document_path
        )
        doc_type = await self.__document_parser.get_doc_type(document_path)

        for idx, payload in chunks:
            record = DBSchema(
                chunk_idx=idx,
                payload=payload,
                doc_path=str(document_path),
                doc_type=doc_type,
                created=creation_datetime,
            )

            await self.__document_store.add_record(record)
