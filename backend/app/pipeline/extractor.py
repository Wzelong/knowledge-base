import asyncio
import base64
from dataclasses import dataclass
from pathlib import Path

from agents import Agent, ModelSettings, Runner, WebSearchTool
from openai.types.shared import Reasoning

from app.pipeline.aggregator import aggregate
from app.pipeline.chunking import PDF_CHUNK_PAGES, TEXT_CHUNK_CHARS, split_pdf, split_text
from app.pipeline.models import Extraction
from app.pipeline.web import fetch_page, fetch_url

EXTRACTION_INSTRUCTIONS = """\
You extract knowledge from documents into a personal knowledge base.

From the document, produce:
1. summary: 3-6 sentences capturing what the document covers and its key takeaways.
2. concepts: the specific ideas, mechanisms, techniques, or named methods the document explains.

The knowledge base accumulates concepts across many documents, so each concept must be precise enough to stand on its own:
- Name each concept the way practitioners would, specific enough to look up (e.g. "gradient checkpointing", not "optimization"). When the document names the concept itself, use that exact term rather than coining your own.
- Skip broad fields and umbrella terms ("machine learning", "AI", "neural networks"): they match everything and distinguish nothing.
- Include only concepts the document explains in enough depth that a reader learns how they work; skip passing mentions.
- Write each description as 1-2 self-contained sentences defining the concept itself, not the document's narration of it ("X is ...", never "the author discusses X").

Most documents yield roughly 3-10 concepts; thin material yields fewer. Return only what clears the bar — never pad to reach a count.

When the input is a link or references content you cannot read directly, retrieve it with the fetch_url tool. If fetching fails, use web search to locate the same content. Extract only from the source content itself — never introduce concepts from search results or pages beyond the given source.
"""

extraction_agent = Agent(
    name="Concept extractor",
    instructions=EXTRACTION_INSTRUCTIONS,
    model="gpt-5.4-mini",
    model_settings=ModelSettings(reasoning=Reasoning(effort="low")),
    tools=[WebSearchTool(), fetch_url],
    output_type=Extraction,
)

SINGLE_NOTE = "Extract the summary and core concepts from the attached document."


@dataclass
class SourceExtraction:
    extraction: Extraction
    parts: int
    input_bytes: int
    title: str | None = None


def is_url(source: str | Path) -> bool:
    return isinstance(source, str) and source.startswith(("http://", "https://"))


def part_note(index: int, total: int) -> str:
    return (
        f"This is part {index} of {total} of a larger document. "
        "Extract the summary and core concepts from this part. "
        "A part consisting mostly of references, acknowledgments, or appendix "
        "material may yield few or no concepts."
    )


def pdf_message(data: bytes, filename: str, note: str) -> list:
    encoded = base64.b64encode(data).decode()
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_file",
                    "filename": filename,
                    "file_data": f"data:application/pdf;base64,{encoded}",
                },
                {"type": "input_text", "text": note},
            ],
        }
    ]


def text_inputs(text: str, text_chunk_chars: int) -> list:
    chunks = split_text(text, text_chunk_chars)
    if len(chunks) == 1:
        return [chunks[0]]
    return [
        f"{part_note(i, len(chunks))}\n\n{chunk}"
        for i, chunk in enumerate(chunks, start=1)
    ]


def build_chunk_inputs(
    path: Path,
    text_chunk_chars: int = TEXT_CHUNK_CHARS,
    pdf_chunk_pages: int = PDF_CHUNK_PAGES,
) -> list:
    if path.suffix.lower() == ".pdf":
        parts = split_pdf(path, pdf_chunk_pages)
        if len(parts) == 1:
            return [pdf_message(parts[0], path.name, SINGLE_NOTE)]
        return [
            pdf_message(part, f"{path.stem}-part{i}.pdf", part_note(i, len(parts)))
            for i, part in enumerate(parts, start=1)
        ]
    return text_inputs(path.read_text(), text_chunk_chars)


async def extract_part(agent_input) -> Extraction:
    result = await Runner.run(extraction_agent, agent_input)
    return result.final_output


async def extract_from_inputs(inputs: list) -> Extraction:
    if len(inputs) == 1:
        return await extract_part(inputs[0])
    extractions = await asyncio.gather(*(extract_part(i) for i in inputs))
    return await aggregate(list(extractions))


async def extract_source(
    source: str | Path,
    text_chunk_chars: int = TEXT_CHUNK_CHARS,
    pdf_chunk_pages: int = PDF_CHUNK_PAGES,
) -> SourceExtraction:
    if is_url(source):
        page = await fetch_page(source)
        if page is None:
            inputs = [
                f"Extract the summary and core concepts from the content at this link: {source}"
            ]
            title, input_bytes = None, 0
        else:
            inputs = text_inputs(page.text, text_chunk_chars)
            title, input_bytes = page.title, len(page.text.encode())
    else:
        path = Path(source)
        inputs = build_chunk_inputs(path, text_chunk_chars, pdf_chunk_pages)
        title, input_bytes = path.stem, path.stat().st_size

    extraction = await extract_from_inputs(inputs)
    return SourceExtraction(
        extraction=extraction, parts=len(inputs), input_bytes=input_bytes, title=title
    )


async def extract_document(
    path: Path,
    text_chunk_chars: int = TEXT_CHUNK_CHARS,
    pdf_chunk_pages: int = PDF_CHUNK_PAGES,
) -> Extraction:
    run = await extract_source(path, text_chunk_chars, pdf_chunk_pages)
    return run.extraction
