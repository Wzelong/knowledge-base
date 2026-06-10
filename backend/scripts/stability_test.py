import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
load_dotenv(".env.local")

from app.pipeline.extractor import is_url
from app.pipeline.ingest import ingest_source
from app.pipeline.store import InMemoryConceptStore


async def main() -> None:
    arg = sys.argv[1]
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    source = arg if is_url(arg) else Path(arg)

    store = InMemoryConceptStore()
    baseline = 0
    times: list[float] = []

    for index in range(1, runs + 1):
        result = await ingest_source(source, store)
        times.append(result.timings["total"])
        print(
            f"run {index}: created {len(result.created)}, merged {len(result.merged)}, "
            f"{result.timings['total']:.1f}s "
            f"(extract {result.timings['extract']:.1f}, dedup {result.timings['dedup']:.1f}), "
            f"parts={result.parts}, input={result.input_bytes / 1024:.1f}KB"
        )
        if index == 1:
            baseline = len(result.created)
        else:
            total = len(result.created) + len(result.merged)
            rate = len(result.merged) / total if total else 0.0
            print(f"  merge rate: {rate:.0%}")
            if result.created:
                print(f"  new names: {result.created}")

    print(f"\nbaseline concepts after run 1: {baseline}")
    print(f"store concepts after {runs} runs: {len(store.concepts)}")
    print(f"duplicate growth: {len(store.concepts) - baseline}")
    print(f"time: mean {sum(times) / len(times):.1f}s, min {min(times):.1f}s, max {max(times):.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
