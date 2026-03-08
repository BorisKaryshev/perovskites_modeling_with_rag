from enum import Enum


class DocumentType(str, Enum):
    UNKNONW = ""
    PDF = "pdf"
    MARKDOWN = "md"
