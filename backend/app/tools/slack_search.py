"""slack_search — keyword search over Slack-style messages."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import SourceType
from app.db.models import SlackMessage
from app.tools.keyword import ilike_any, keyword_score, terms
from app.tools.schemas import Evidence


async def search_slack(
    session: AsyncSession,
    query: str,
    *,
    channel: str | None = None,
    limit: int = 5,
) -> list[Evidence]:
    """Find Slack messages matching the query, optionally within a channel."""
    query_terms = terms(query)
    if not query_terms:
        return []

    stmt = select(SlackMessage).where(ilike_any(query_terms, SlackMessage.text))
    if channel:
        stmt = stmt.where(SlackMessage.channel == channel)

    messages = (await session.execute(stmt.limit(limit * 3))).scalars().all()

    results = [
        Evidence(
            source_type=SourceType.SLACK,
            source_ref=msg.thread_id,  # human-readable slug experts cite (e.g. "t-rel-1")
            title=f"#{msg.channel} — {msg.author}",
            snippet=msg.text,
            score=keyword_score(msg.text, query_terms),
            metadata={"thread_id": msg.thread_id, "channel": msg.channel, "author": msg.author},
        )
        for msg in messages
    ]
    results.sort(key=lambda e: e.score or 0.0, reverse=True)
    return results[:limit]
