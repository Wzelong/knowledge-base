import io
from pathlib import Path

from pypdf import PdfReader, PdfWriter

TEXT_CHUNK_CHARS = 20000
PDF_CHUNK_PAGES = 12


def split_text(text: str, chunk_chars: int = TEXT_CHUNK_CHARS) -> list[str]:
    if len(text) <= chunk_chars:
        return [text]
    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if current and len(candidate) > chunk_chars:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def split_pdf(path: Path, chunk_pages: int = PDF_CHUNK_PAGES) -> list[bytes]:
    reader = PdfReader(path)
    if len(reader.pages) <= chunk_pages:
        return [path.read_bytes()]
    parts: list[bytes] = []
    for start in range(0, len(reader.pages), chunk_pages):
        writer = PdfWriter()
        for page in reader.pages[start : start + chunk_pages]:
            writer.add_page(page)
        buffer = io.BytesIO()
        writer.write(buffer)
        parts.append(buffer.getvalue())
    return parts
