import asyncio
import itertools
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
load_dotenv(".env.local")

from agents import Agent, ModelSettings, Runner
from openai.types.shared import Reasoning

from app.pipeline.embeddings import concept_text, embed_batch
from app.pipeline.extractor import extract_document
from app.pipeline.store import cosine_similarity

paraphrase_agent = Agent(
    name="Paraphraser",
    instructions=(
        "Rewrite the given concept description in different words, as if it were "
        "extracted from a different document about the same topic. Keep the meaning, "
        "change the phrasing. Respond with the rewritten description only."
    ),
    model="gpt-5.4-mini",
    model_settings=ModelSettings(reasoning=Reasoning(effort="low")),
)


async def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "../data/transformer.txt")
    extraction = await extract_document(path)
    names = [c.name for c in extraction.concepts]
    originals = [concept_text(c.name, c.description) for c in extraction.concepts]

    paraphrase_runs = await asyncio.gather(
        *[Runner.run(paraphrase_agent, text) for text in originals]
    )
    rewritten = [
        concept_text(name, run.final_output.strip())
        for name, run in zip(names, paraphrase_runs)
    ]

    vectors = await embed_batch(originals + rewritten)
    original_vectors = vectors[: len(originals)]
    rewritten_vectors = vectors[len(originals) :]

    same_pairs = sorted(
        (
            (cosine_similarity(original_vectors[i], rewritten_vectors[i]), names[i])
            for i in range(len(names))
        ),
    )
    cross_pairs = sorted(
        (
            (cosine_similarity(original_vectors[i], original_vectors[j]), names[i], names[j])
            for i, j in itertools.combinations(range(len(names)), 2)
        ),
        reverse=True,
    )

    print("Same concept, paraphrased (should merge — must sit ABOVE threshold):")
    for similarity, name in same_pairs:
        print(f"  {similarity:.3f}  {name}")

    print("\nDifferent concepts, same document (should stay separate — must sit BELOW threshold):")
    for similarity, a, b in cross_pairs[:12]:
        print(f"  {similarity:.3f}  {a}  <->  {b}")

    min_same = same_pairs[0][0]
    max_cross = cross_pairs[0][0]
    print(f"\nmin same-concept similarity: {min_same:.3f}")
    print(f"max cross-concept similarity: {max_cross:.3f}")
    if max_cross < min_same:
        print(f"suggested threshold (midpoint): {(min_same + max_cross) / 2:.3f}")
    else:
        print("overlap detected — inspect the pairs above before picking a threshold")


if __name__ == "__main__":
    asyncio.run(main())
