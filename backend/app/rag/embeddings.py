"""Embedding generation via fastembed (CPU, no API key). See ADR 0008.

`bge-small-en-v1.5` is asymmetric: documents and queries use different prefixes.
fastembed exposes `embed()` for documents and `query_embed()` for queries — we use both
so retrieval quality matches how the corpus was indexed.
"""

from functools import lru_cache
from typing import cast

from fastembed import TextEmbedding

from app.core.config import get_settings


@lru_cache
def _model() -> TextEmbedding:
    """Load (and cache) the embedding model. First call downloads it once."""
    return TextEmbedding(model_name=get_settings().embedding_model)


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed passages for storage/indexing."""
    return [vec.tolist() for vec in _model().embed(texts)]


def embed_query(text: str) -> list[float]:
    """Embed a single search query."""
    return cast(list[float], next(iter(_model().query_embed(text))).tolist())
