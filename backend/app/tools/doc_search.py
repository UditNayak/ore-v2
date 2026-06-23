"""doc_search — semantic RAG over document chunks via pgvector cosine similarity."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import SourceType
from app.db.models import Document, DocumentChunk
from app.rag.embeddings import embed_query
from app.tools.schemas import Evidence


async def search_docs(
    session: AsyncSession,
    query: str,
    *,
    k: int | None = None,
) -> list[Evidence]:
    """Return the top-k most semantically similar document chunks as evidence."""
    top_k = k or get_settings().rag_top_k
    query_vec = embed_query(query)

    distance = DocumentChunk.embedding.cosine_distance(query_vec).label("distance")
    stmt = (
        select(DocumentChunk, Document.title, Document.doc_type, Document.service, distance)
        .join(Document, DocumentChunk.document_id == Document.id)
        .order_by(distance)
        .limit(top_k)
    )
    rows = (await session.execute(stmt)).all()

    return [
        Evidence(
            source_type=SourceType.DOC,
            source_ref=str(chunk.document_id),
            title=title,
            snippet=chunk.content,
            score=round(1.0 - float(dist), 4),  # cosine similarity
            metadata={"doc_type": doc_type, "service": service, "chunk_index": chunk.chunk_index},
        )
        for chunk, title, doc_type, service, dist in rows
    ]
