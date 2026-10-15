"""Extract text from supported uploaded documents."""
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}


@dataclass(frozen=True)
class PageText:
    text: str
    page: int | None = None


@dataclass(frozen=True)
class LoadedDocument:
    filename: str
    content_hash: str
    pages: list[PageText]

    @property
    def text(self) -> str:
        return "\n\n".join(p.text for p in self.pages).strip()


def stable_document_id(content_hash: str, filename: str) -> str:
    """Content hash plus normalized name keeps same-named uploads distinct."""
    normalized = Path(filename).name.casefold()
    return hashlib.sha256(f"{normalized}\0{content_hash}".encode("utf-8")).hexdigest()


def _read_upload(upload: bytes | BinaryIO) -> bytes:
    if isinstance(upload, bytes):
        return upload
    if hasattr(upload, "getvalue"):
        return upload.getvalue()
    upload.seek(0)
    return upload.read()


def load_document(filename: str, upload: bytes | BinaryIO) -> LoadedDocument:
    name = Path(filename).name
    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix or '(no extension)'}")
    payload = _read_upload(upload)
    digest = hashlib.sha256(payload).hexdigest()
    if not payload:
        raise ValueError("The document is empty.")
    if suffix == ".pdf":
        try:
            reader = PdfReader(__import__("io").BytesIO(payload), strict=False)
            if reader.is_encrypted:
                try:
                    if not reader.decrypt(""):
                        raise ValueError("This PDF is encrypted and cannot be opened.")
                except Exception as exc:
                    raise ValueError("This PDF is encrypted and cannot be opened.") from exc
            pages = [PageText((page.extract_text() or "").strip(), i + 1)
                     for i, page in enumerate(reader.pages)]
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("Could not read this PDF. It may be malformed or encrypted.") from exc
        if not any(p.text for p in pages):
            raise ValueError("No selectable text was found. Scanned PDFs need OCR, which is not included.")
    else:
        try:
            text = payload.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("Text document is not valid UTF-8.") from exc
        pages = [PageText(text.strip())]
    if not any(p.text for p in pages):
        raise ValueError("The document contains no text.")
    return LoadedDocument(name, digest, pages)
