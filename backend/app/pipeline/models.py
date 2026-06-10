from pydantic import BaseModel


class ExtractedConcept(BaseModel):
    name: str
    description: str


class Extraction(BaseModel):
    summary: str
    concepts: list[ExtractedConcept]


class SourceMetadata(BaseModel):
    title: str
    source_type: str
    origin: str | None = None


class ConceptMatch(BaseModel):
    id: str
    name: str
    description: str
    similarity: float
