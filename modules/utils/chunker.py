from typing import List
from dataclasses import dataclass
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.config import logger

@dataclass
class Chunk:
    file: str
    text: str

class ParagraphMarkdownChunker:
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 1000):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            # mặc định separators already ["\n\n", "\n", " ", ""]
            length_function=len,
            is_separator_regex=False,
        )

    def chunk(self, md_text: str, source_file: str) -> List[Chunk]:
        texts = self.text_splitter.split_text(md_text)
        chunks = [Chunk(file=source_file, text=text) for text in texts]
        logger.info(f"Paragraph-based chunked into {len(chunks)} from {source_file}")
        return chunks
