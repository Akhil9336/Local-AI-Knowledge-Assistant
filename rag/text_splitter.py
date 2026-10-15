"""Deterministic paragraph-aware chunking with overlap."""
from dataclasses import dataclass
import re
from .document_loader import PageText


@dataclass(frozen=True)
class TextChunk:
    text: str
    chunk_number: int
    page: int | None = None


def split_pages(pages: list[PageText], chunk_size: int = 1000,
                overlap: int = 150) -> list[TextChunk]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Require chunk_size > overlap >= 0.")
    chunks: list[TextChunk] = []
    for page in pages:
        text = page.text.strip()
        if not text:
            continue
        if not re.search(r"\s", text) and len(text) > chunk_size:
            start = 0
            while start < len(text):
                end = min(start + chunk_size, len(text))
                chunks.append(TextChunk(text[start:end], len(chunks), page.page))
                if end == len(text):
                    break
                start = end - overlap
            continue
        # Keep paragraphs together when practical, then split oversized paragraphs
        # near sentence/word boundaries. This gives retrieval more complete facts.
        paragraphs = [p.strip() for p in text.splitlines() if p.strip()]
        units: list[str] = []
        for paragraph in paragraphs:
            if len(paragraph) <= chunk_size:
                units.append(paragraph)
                continue
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            for sentence in sentences:
                while len(sentence) > chunk_size:
                    cut = sentence.rfind(" ", 0, chunk_size + 1)
                    if cut < chunk_size // 2:
                        cut = chunk_size
                    units.append(sentence[:cut].strip())
                    sentence = sentence[cut:].strip()
                if sentence:
                    units.append(sentence)

        current = ""
        for unit in units:
            candidate = f"{current}\n{unit}" if current else unit
            if len(candidate) <= chunk_size:
                current = candidate
                continue
            if current:
                chunks.append(TextChunk(current, len(chunks), page.page))
                tail = current[-overlap:].strip() if overlap else ""
                current = f"{tail}\n{unit}" if tail and len(tail) + len(unit) + 1 <= chunk_size else unit
            else:
                current = unit
        if current:
            chunks.append(TextChunk(current, len(chunks), page.page))
    return chunks
