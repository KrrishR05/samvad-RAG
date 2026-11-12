"""
SAMVAD Ingestion — Document Loaders

Parses TXT, Markdown, PDF (PyMuPDF), DOCX (python-docx), HTML, and JSON
into normalized text with source provenance.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Optional

from app.core.errors import InputValidationError
from app.ingestion.normalizer import normalize_text, sha256_text

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {".txt", ".md", ".markdown", ".pdf", ".docx", ".html", ".htm", ".json"}
)


@dataclass
class LoadedDocument:
    """Normalized document extracted from a file or byte payload."""

    filename: str
    media_type: str
    content: str
    content_hash: str
    language: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class _TextHTMLParser(HTMLParser):
    """Minimal stdlib HTML-to-text extractor ignoring script/style tags."""

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip_depth += 1
        elif tag.lower() in {"p", "br", "div", "li", "h1", "h2", "h3", "h4", "tr"}:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def _decode_text_bytes(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "utf-16"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _extract_pdf_bytes(raw: bytes) -> tuple[str, dict[str, Any]]:
    import pymupdf  # type: ignore[import-untyped]

    pages_text: list[str] = []
    with pymupdf.open(stream=raw, filetype="pdf") as doc:
        page_count = len(doc)
        for page_idx, page in enumerate(doc):
            txt = page.get_text("text")
            if txt and txt.strip():
                pages_text.append(txt)
    return "\n\n".join(pages_text), {"page_count": page_count}


def _extract_docx_bytes(raw: bytes) -> str:
    import io
    from docx import Document  # type: ignore[import-untyped]

    document = Document(io.BytesIO(raw))
    paragraphs = [p.text for p in document.paragraphs if p.text and p.text.strip()]
    return "\n\n".join(paragraphs)


def _extract_html_bytes(raw: bytes) -> str:
    parser = _TextHTMLParser()
    parser.feed(_decode_text_bytes(raw))
    parser.close()
    return parser.get_text()


def _extract_json_bytes(raw: bytes) -> str:
    parsed = json.loads(_decode_text_bytes(raw))
    if isinstance(parsed, str):
        return parsed
    return json.dumps(parsed, ensure_ascii=False, indent=2)


def load_document_bytes(
    *,
    filename: str,
    raw_bytes: bytes,
    language: Optional[str] = None,
    max_bytes: int = 25 * 1024 * 1024,
) -> LoadedDocument:
    """
    Validate and parse raw uploaded bytes into a normalized LoadedDocument.

    Raises:
        InputValidationError: On empty payload, oversized file, or unsupported format.
    """
    safe_name = Path(filename).name
    if not safe_name:
        raise InputValidationError("Filename must not be empty.")
    if not raw_bytes:
        raise InputValidationError(f"Uploaded file '{safe_name}' is empty.")
    if len(raw_bytes) > max_bytes:
        raise InputValidationError(
            f"Uploaded file '{safe_name}' exceeds {max_bytes} bytes limit."
        )

    ext = Path(safe_name).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise InputValidationError(
            f"Unsupported document extension '{ext}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    extra_meta: dict[str, Any] = {}
    if ext in {".txt", ".md", ".markdown"}:
        raw_text = _decode_text_bytes(raw_bytes)
        media_type = "text/markdown" if ext in {".md", ".markdown"} else "text/plain"
    elif ext == ".pdf":
        raw_text, extra_meta = _extract_pdf_bytes(raw_bytes)
        media_type = "application/pdf"
    elif ext == ".docx":
        raw_text = _extract_docx_bytes(raw_bytes)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif ext in {".html", ".htm"}:
        raw_text = _extract_html_bytes(raw_bytes)
        media_type = "text/html"
    elif ext == ".json":
        raw_text = _extract_json_bytes(raw_bytes)
        media_type = "application/json"
    else:  # pragma: no cover
        raise InputValidationError(f"Unsupported extension '{ext}'.")

    normalized = normalize_text(raw_text)
    if not normalized:
        raise InputValidationError(
            f"No extractable text content found in '{safe_name}'."
        )

    return LoadedDocument(
        filename=safe_name,
        media_type=media_type,
        content=normalized,
        content_hash=sha256_text(normalized),
        language=language,
        metadata=extra_meta,
    )


def load_document_file(
    path: Path,
    *,
    language: Optional[str] = None,
    max_bytes: int = 25 * 1024 * 1024,
) -> LoadedDocument:
    """Load and parse a document from a filesystem path."""
    if not path.is_file():
        raise FileNotFoundError(f"Document file not found: {path}")
    return load_document_bytes(
        filename=path.name,
        raw_bytes=path.read_bytes(),
        language=language,
        max_bytes=max_bytes,
    )

