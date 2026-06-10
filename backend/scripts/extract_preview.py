import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
load_dotenv(".env.local")

from app.pipeline.chunking import PDF_CHUNK_PAGES, TEXT_CHUNK_CHARS
from app.pipeline.extractor import build_chunk_inputs, extract_document


async def main() -> None:
    path = Path(sys.argv[1])
    text_chunk_chars = int(sys.argv[2]) if len(sys.argv) > 2 else TEXT_CHUNK_CHARS
    pdf_chunk_pages = int(sys.argv[3]) if len(sys.argv) > 3 else PDF_CHUNK_PAGES

    parts = len(build_chunk_inputs(path, text_chunk_chars, pdf_chunk_pages))
    print(f"Parts: {parts}\n")

    extraction = await extract_document(path, text_chunk_chars, pdf_chunk_pages)
    print(f"Summary:\n{extraction.summary}\n")
    print(f"Concepts ({len(extraction.concepts)}):")
    for concept in extraction.concepts:
        print(f"- {concept.name}: {concept.description}")


if __name__ == "__main__":
    asyncio.run(main())
