import time
from dataclasses import dataclass, field
from pathlib import Path

from app.pipeline.embeddings import concept_text, embed_batch
from app.pipeline.extractor import extract_source, is_url
from app.pipeline.merger import is_same_concept, merge_descriptions
from app.pipeline.models import ConceptMatch, ExtractedConcept, SourceMetadata
from app.pipeline.store import ConceptStore

AUTO_MERGE_THRESHOLD = 0.92
CANDIDATE_THRESHOLD = 0.70


@dataclass
class IngestResult:
    source_id: str
    summary: str
    parts: int
    input_bytes: int
    timings: dict[str, float]
    created: list[str] = field(default_factory=list)
    merged: list[dict] = field(default_factory=list)


def default_metadata(source: str | Path, title: str | None) -> SourceMetadata:
    if is_url(source):
        return SourceMetadata(title=title or str(source), source_type="url", origin=str(source))
    path = Path(source)
    return SourceMetadata(
        title=path.stem,
        source_type=path.suffix.lstrip(".") or "text",
        origin=str(path),
    )


async def should_merge(match: ConceptMatch | None, concept: ExtractedConcept) -> bool:
    if match is None or match.similarity < CANDIDATE_THRESHOLD:
        return False
    if match.similarity >= AUTO_MERGE_THRESHOLD:
        return True
    verdict = await is_same_concept(
        match.name, match.description, concept.name, concept.description
    )
    return verdict.same_concept


async def ingest_source(
    source: str | Path,
    store: ConceptStore,
    metadata: SourceMetadata | None = None,
) -> IngestResult:
    timings: dict[str, float] = {}
    total_start = time.perf_counter()

    stage_start = time.perf_counter()
    run = await extract_source(source)
    timings["extract"] = time.perf_counter() - stage_start
    extraction = run.extraction

    stage_start = time.perf_counter()
    embeddings = await embed_batch(
        [concept_text(c.name, c.description) for c in extraction.concepts]
    )
    timings["embed"] = time.perf_counter() - stage_start

    metadata = metadata or default_metadata(source, run.title)
    source_id = store.add_source(metadata, extraction.summary)
    result = IngestResult(
        source_id=source_id,
        summary=extraction.summary,
        parts=run.parts,
        input_bytes=run.input_bytes,
        timings=timings,
    )

    stage_start = time.perf_counter()
    for concept, embedding in zip(extraction.concepts, embeddings):
        matches = store.find_similar(embedding, top_k=1)
        match = matches[0] if matches else None
        if match and await should_merge(match, concept):
            merged = await merge_descriptions(match.name, match.description, concept.description)
            if merged != match.description:
                new_embedding = (await embed_batch([concept_text(match.name, merged)]))[0]
                store.update_concept(match.id, merged, new_embedding)
            store.link_source(match.id, source_id, concept.description)
            result.merged.append(
                {
                    "new": concept.name,
                    "existing": match.name,
                    "similarity": round(match.similarity, 3),
                }
            )
        else:
            concept_id = store.insert_concept(concept.name, concept.description, embedding)
            store.link_source(concept_id, source_id, concept.description)
            result.created.append(concept.name)
    timings["dedup"] = time.perf_counter() - stage_start

    timings["total"] = time.perf_counter() - total_start
    return result
