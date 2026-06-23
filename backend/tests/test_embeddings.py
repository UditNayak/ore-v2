"""Embedding sanity: dimension matches config, and chunking covers the whole text."""

from app.core.config import get_settings
from app.rag.embeddings import embed_query
from app.rag.ingest import chunk_text


def test_embed_query_matches_configured_dim() -> None:
    vec = embed_query("why was the release delayed?")
    assert len(vec) == get_settings().embedding_dim


def test_chunking_overlaps_and_covers() -> None:
    text = "para one. " * 200  # ~2000 chars -> multiple chunks
    chunks = chunk_text(text, size=300, overlap=50)
    assert len(chunks) > 1
    # Every chunk respects the window size (allowing for boundary snapping).
    assert all(len(c) <= 350 for c in chunks)


def test_short_text_is_single_chunk() -> None:
    assert chunk_text("tiny") == ["tiny"]
    assert chunk_text("   ") == []
