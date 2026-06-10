from functools import lru_cache

from openai import AsyncOpenAI

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


@lru_cache
def get_openai() -> AsyncOpenAI:
    return AsyncOpenAI()


def concept_text(name: str, description: str) -> str:
    return f"{name}: {description}"


async def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    response = await get_openai().embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]
