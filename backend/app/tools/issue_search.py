"""issue_search — structured + keyword search over the issue tracker."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import SourceType
from app.db.models import Issue
from app.tools.keyword import ilike_any, keyword_score, terms
from app.tools.schemas import Evidence


async def search_issues(
    session: AsyncSession,
    query: str,
    *,
    status: str | None = None,
    owner: str | None = None,
    service: str | None = None,
    limit: int = 5,
) -> list[Evidence]:
    """Find issues matching the query text, optionally filtered by structured fields."""
    query_terms = terms(query)
    stmt = select(Issue)
    if query_terms:
        stmt = stmt.where(ilike_any(query_terms, Issue.title, Issue.description))
    if status:
        stmt = stmt.where(Issue.status == status)
    if owner:
        stmt = stmt.where(Issue.owner == owner)
    if service:
        stmt = stmt.where(Issue.service == service)

    issues = (await session.execute(stmt.limit(limit * 3))).scalars().all()

    results = [
        Evidence(
            source_type=SourceType.ISSUE,
            source_ref=issue.key,
            title=issue.title,
            snippet=issue.description,
            score=keyword_score(f"{issue.title} {issue.description}", query_terms),
            metadata={
                "status": issue.status,
                "owner": issue.owner,
                "service": issue.service,
                "labels": issue.labels,
            },
        )
        for issue in issues
    ]
    results.sort(key=lambda e: e.score or 0.0, reverse=True)
    return results[:limit]
