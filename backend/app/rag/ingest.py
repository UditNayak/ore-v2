"""Document chunking + ingestion into pgvector. See docs/RETRIEVAL.md."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, DocumentChunk
from app.rag.embeddings import embed_documents

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks, preferring paragraph boundaries.

    Overlap preserves context across boundaries so evidence snippets stay coherent.
    """
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        # Prefer to break on a paragraph/sentence boundary near the end of the window.
        if end < len(text):
            window = text[start:end]
            for sep in ("\n\n", "\n", ". "):
                idx = window.rfind(sep)
                if idx != -1 and idx > size // 2:
                    end = start + idx + len(sep)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


async def ingest_document(session: AsyncSession, document: Document) -> int:
    """Chunk a (already-added) document, embed the chunks, and persist them.

    Returns the number of chunks created.
    """
    chunks = chunk_text(document.content)
    if not chunks:
        return 0
    vectors = embed_documents(chunks)
    for index, (content, vector) in enumerate(zip(chunks, vectors, strict=True)):
        session.add(
            DocumentChunk(
                document=document,
                chunk_index=index,
                content=content,
                embedding=vector,
            )
        )
    return len(chunks)
