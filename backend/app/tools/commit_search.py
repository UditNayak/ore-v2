"""commit_search — keyword search over commit history, with optional service filter."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import SourceType
from app.db.models import Commit
from app.tools.keyword import ilike_any, keyword_score, terms
from app.tools.schemas import Evidence


async def search_commits(
    session: AsyncSession,
    query: str,
    *,
    service: str | None = None,
    limit: int = 5,
) -> list[Evidence]:
    """Find commits whose message matches the query, optionally within a service."""
    query_terms = terms(query)
    stmt = select(Commit)
    if query_terms:
        stmt = stmt.where(ilike_any(query_terms, Commit.message))
    if service:
        stmt = stmt.where(Commit.service == service)

    commits = (await session.execute(stmt.limit(limit * 3))).scalars().all()

    results = [
        Evidence(
            source_type=SourceType.COMMIT,
            source_ref=commit.sha,
            title=f"{commit.message[:60]} — {commit.author}",
            snippet=commit.message,
            score=keyword_score(commit.message, query_terms),
            metadata={"author": commit.author, "service": commit.service, "files": commit.files},
        )
        for commit in commits
    ]
    results.sort(key=lambda e: e.score or 0.0, reverse=True)
    return results[:limit]
