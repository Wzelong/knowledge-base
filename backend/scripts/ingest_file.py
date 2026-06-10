import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
load_dotenv(".env.local")

from app.pipeline.extractor import is_url
from app.pipeline.ingest import ingest_source
from app.pipeline.store import InMemoryConceptStore


def print_result(label: str, result) -> None:
    timings = result.timings
    print(f"\n{label}")
    print(f"  summary: {result.summary[:160]}...")
    print(
        f"  input: {result.input_bytes / 1024:.1f}KB, parts: {result.parts}, "
        f"time: {timings['total']:.1f}s "
        f"(extract {timings['extract']:.1f}, embed {timings['embed']:.1f}, dedup {timings['dedup']:.1f})"
    )
    print(f"  created ({len(result.created)}): {result.created}")
    print(f"  merged ({len(result.merged)}):")
    for entry in result.merged:
        print(f"    {entry['new']} -> {entry['existing']} ({entry['similarity']})")


async def main() -> None:
    store = InMemoryConceptStore()

    for index, arg in enumerate(sys.argv[1:], start=1):
        source = arg if is_url(arg) else Path(arg)
        result = await ingest_source(source, store)
        print_result(f"Ingest {index}: {arg}", result)

    print(f"\nConcepts in store: {len(store.concepts)}")
    for concept in store.concepts.values():
        print(f"- {concept['name']}: {concept['description']}")


if __name__ == "__main__":
    asyncio.run(main())
