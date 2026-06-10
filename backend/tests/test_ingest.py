import asyncio
from pathlib import Path

import pytest

from app.pipeline import ingest as ingest_module
from app.pipeline.extractor import SourceExtraction
from app.pipeline.ingest import ingest_source
from app.pipeline.merger import SameConceptVerdict
from app.pipeline.models import ExtractedConcept, Extraction
from app.pipeline.store import InMemoryConceptStore

ATTENTION = [1.0, 0.0, 0.0]
ATTENTION_REWORDED = [0.95, 0.31225, 0.0]
ATTENTION_BORDERLINE = [0.8, 0.6, 0.0]
SOFTMAX = [0.0, 1.0, 0.0]
TOKENIZATION = [0.0, 0.0, 1.0]

VECTORS = {
    "attention: weighs context words": ATTENTION,
    "attention: contextual word weighting": ATTENTION_REWORDED,
    "attention: merged description": ATTENTION,
    "self-attention: tokens attend to each other": ATTENTION_BORDERLINE,
    "softmax: scores to probabilities": SOFTMAX,
    "tokenization: text to tokens": TOKENIZATION,
}


def fake_extraction(*concepts: tuple[str, str]) -> Extraction:
    return Extraction(
        summary="summary",
        concepts=[ExtractedConcept(name=n, description=d) for n, d in concepts],
    )


@pytest.fixture
def pipeline(monkeypatch):
    state = {"extraction": None, "same_concept": True, "judge_calls": 0}

    async def fake_extract_source(source, **kwargs) -> SourceExtraction:
        return SourceExtraction(
            extraction=state["extraction"], parts=1, input_bytes=1024, title="title"
        )

    async def fake_embed_batch(texts: list[str]) -> list[list[float]]:
        return [VECTORS[text] for text in texts]

    async def fake_merge(name: str, existing: str, new: str) -> str:
        return "merged description"

    async def fake_judge(*args) -> SameConceptVerdict:
        state["judge_calls"] += 1
        return SameConceptVerdict(same_concept=state["same_concept"], reason="test")

    monkeypatch.setattr(ingest_module, "extract_source", fake_extract_source)
    monkeypatch.setattr(ingest_module, "embed_batch", fake_embed_batch)
    monkeypatch.setattr(ingest_module, "merge_descriptions", fake_merge)
    monkeypatch.setattr(ingest_module, "is_same_concept", fake_judge)
    return state


def test_new_concepts_are_created(pipeline):
    store = InMemoryConceptStore()
    pipeline["extraction"] = fake_extraction(
        ("attention", "weighs context words"),
        ("softmax", "scores to probabilities"),
    )

    result = asyncio.run(ingest_source(Path("doc.txt"), store))

    assert result.created == ["attention", "softmax"]
    assert result.merged == []
    assert len(store.concepts) == 2
    assert len(store.concept_sources) == 2
    assert store.sources[result.source_id]["summary"] == "summary"
    assert set(result.timings) == {"extract", "embed", "dedup", "total"}


def test_url_source_metadata(pipeline):
    store = InMemoryConceptStore()
    pipeline["extraction"] = fake_extraction(("attention", "weighs context words"))

    result = asyncio.run(ingest_source("https://example.com/post", store))

    metadata = store.sources[result.source_id]["metadata"]
    assert metadata.source_type == "url"
    assert metadata.origin == "https://example.com/post"
    assert metadata.title == "title"


def test_high_similarity_auto_merges_and_reembeds(pipeline):
    store = InMemoryConceptStore()
    pipeline["extraction"] = fake_extraction(("attention", "weighs context words"))
    asyncio.run(ingest_source(Path("first.txt"), store))

    pipeline["extraction"] = fake_extraction(("attention", "contextual word weighting"))
    result = asyncio.run(ingest_source(Path("second.txt"), store))

    assert result.created == []
    assert len(result.merged) == 1
    assert result.merged[0]["existing"] == "attention"
    assert pipeline["judge_calls"] == 0

    assert len(store.concepts) == 1
    concept = next(iter(store.concepts.values()))
    assert concept["description"] == "merged description"
    assert concept["embedding"] == ATTENTION

    source_descriptions = [link["description"] for link in store.concept_sources]
    assert source_descriptions == ["weighs context words", "contextual word weighting"]


def test_borderline_merges_when_judge_confirms(pipeline):
    store = InMemoryConceptStore()
    pipeline["extraction"] = fake_extraction(("attention", "weighs context words"))
    asyncio.run(ingest_source(Path("first.txt"), store))

    pipeline["extraction"] = fake_extraction(("self-attention", "tokens attend to each other"))
    pipeline["same_concept"] = True
    result = asyncio.run(ingest_source(Path("second.txt"), store))

    assert pipeline["judge_calls"] == 1
    assert result.created == []
    assert len(result.merged) == 1
    assert len(store.concepts) == 1


def test_borderline_stays_separate_when_judge_rejects(pipeline):
    store = InMemoryConceptStore()
    pipeline["extraction"] = fake_extraction(("attention", "weighs context words"))
    asyncio.run(ingest_source(Path("first.txt"), store))

    pipeline["extraction"] = fake_extraction(("self-attention", "tokens attend to each other"))
    pipeline["same_concept"] = False
    result = asyncio.run(ingest_source(Path("second.txt"), store))

    assert pipeline["judge_calls"] == 1
    assert result.created == ["self-attention"]
    assert result.merged == []
    assert len(store.concepts) == 2


def test_below_candidate_threshold_skips_judge(pipeline):
    store = InMemoryConceptStore()
    pipeline["extraction"] = fake_extraction(("attention", "weighs context words"))
    asyncio.run(ingest_source(Path("first.txt"), store))

    pipeline["extraction"] = fake_extraction(("tokenization", "text to tokens"))
    result = asyncio.run(ingest_source(Path("second.txt"), store))

    assert pipeline["judge_calls"] == 0
    assert result.created == ["tokenization"]
    assert result.merged == []
    assert len(store.concepts) == 2
