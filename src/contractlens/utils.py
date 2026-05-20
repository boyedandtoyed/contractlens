"""PDF parsing and text utilities for ContractLens."""
from __future__ import annotations

import io
import re


def extract_text_from_pdf(content: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def clean_text(text: str) -> str:
    text = re.sub(r"[^\x20-\x7E\n\t]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_paragraphs(text: str, min_length: int = 40) -> list[str]:
    chunks = re.split(r"\n{2,}|(?<=[.!?])\s{2,}", text)
    return [c.strip() for c in chunks if len(c.strip()) >= min_length]
