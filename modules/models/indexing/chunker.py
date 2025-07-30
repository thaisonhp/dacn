# chunker.py
import re
from typing import List
from dataclasses import dataclass
from pathlib import Path
from core.config import logger

@dataclass
class Chunk:
    file: str
    heading: str
    text: str


class MarkdownChunker:
    def chunk(self, md_text: str, source_file: str) -> List[Chunk]:
        chunks, current = [], {"heading": "", "text": []}
        for line in md_text.splitlines():
            hdr = re.match(r"^(#{1,6})\s*(.*)", line)
            if hdr:
                if current["text"]:
                    chunks.append(
                        Chunk(
                            file=source_file,
                            heading=current["heading"],
                            text="\n".join(current["text"]),
                        )
                    )
                current = {"heading": hdr.group(2).strip(), "text": []}
            else:
                current["text"].append(line)
        if current["text"]:
            chunks.append(
                Chunk(
                    file=source_file,
                    heading=current["heading"],
                    text="\n".join(current["text"]),
                )
            )
        logger.info(f"Chunked {len(chunks)} sections from {source_file}")
        return chunks
