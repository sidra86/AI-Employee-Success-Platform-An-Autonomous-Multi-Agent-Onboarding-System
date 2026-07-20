"""PDF text extraction helpers."""

from __future__ import annotations

import io
from typing import Union


def extract_text_from_pdf(source: Union[str, bytes, io.BytesIO]) -> str:
    """Extract plain text from a PDF path or bytes. Uses pypdf when available."""
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "PDF support requires pypdf. Install with: pip install pypdf"
            ) from exc

    if isinstance(source, (bytes, bytearray)):
        reader = PdfReader(io.BytesIO(source))
    elif isinstance(source, io.BytesIO):
        reader = PdfReader(source)
    else:
        reader = PdfReader(str(source))

    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n\n".join(pages).strip()
