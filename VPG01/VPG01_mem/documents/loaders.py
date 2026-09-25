from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader
from docx import Document

from config import CHUNK_OVERLAP, CHUNK_SIZE

SUPPORTED_SUFFIXES = {".pdf", ".docx", ".txt"}


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _from_pdf(path)
    if suffix == ".docx":
        return _from_docx(path)
    if suffix == ".txt":
        return _from_txt(path)
    raise ValueError(f"Формат {suffix} не поддерживается. Загрузите PDF, DOCX или TXT.")


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Режет текст на перекрывающиеся куски, стараясь не рвать абзацы посредине."""
    cleaned = "\n".join(line.strip() for line in text.splitlines()).strip()
    if not cleaned:
        return []

    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [cleaned]

    chunks: list[str] = []
    buffer = ""

    for paragraph in paragraphs:
        candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if len(candidate) <= chunk_size:
            buffer = candidate
            continue
        if buffer:
            chunks.append(buffer)
        if len(paragraph) <= chunk_size:
            buffer = paragraph
            continue
        chunks.extend(_split_long(paragraph, chunk_size, overlap))
        buffer = ""

    if buffer:
        chunks.append(buffer)

    if overlap <= 0 or len(chunks) <= 1:
        return chunks

    overlapped: list[str] = []
    for index, chunk in enumerate(chunks):
        if index == 0:
            overlapped.append(chunk)
            continue
        prefix = chunks[index - 1][-overlap:]
        overlapped.append(f"{prefix}\n{chunk}".strip())
    return overlapped


def _from_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages.append(page_text)
    return "\n\n".join(pages)


def _from_docx(path: Path) -> str:
    document = Document(str(path))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def _from_txt(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _split_long(text: str, chunk_size: int, overlap: int) -> list[str]:
    parts: list[str] = []
    start = 0
    step = max(chunk_size - overlap, 1)
    while start < len(text):
        parts.append(text[start : start + chunk_size].strip())
        start += step
    return [part for part in parts if part]
