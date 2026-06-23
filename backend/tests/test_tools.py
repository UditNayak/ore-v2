"""Critical-path tests for the four evidence tools against the seeded corpus.

These are the things that would fail silently: semantic retrieval finding the right
document, structured filters working, and every tool returning a uniform Evidence shape.
"""

from app.core.enums import SourceType
from app.db.models import Issue
from app.tools import search_commits, search_docs, search_issues, search_slack
from app.tools.schemas import Evidence


async def test_doc_search_finds_release_delay_cause(session) -> None:
    results = await search_docs(session, "why was release v2.4 delayed?")
    assert results, "expected at least one document chunk"
    assert all(isinstance(r, Evidence) and r.source_type == SourceType.DOC for r in results)
    blob = " ".join(r.snippet.lower() for r in results)
    assert "v2.4" in blob or "billing" in blob
    # Vector results are similarity-ordered (descending score).
    scores = [r.score for r in results if r.score is not None]
    assert scores == sorted(scores, reverse=True)


async def test_issue_search_keyword_finds_blocker(session) -> None:
    results = await search_issues(session, "billing migration test")
    assert any(r.source_ref == "NIM-412" for r in results)
    assert all(r.source_type == SourceType.ISSUE for r in results)


async def test_issue_search_structured_filter(session) -> None:
    from sqlalchemy import select

    results = await search_issues(session, "reporting", status="blocked")
    # Every returned issue must actually be blocked (structured filter applied).
    keys = {r.source_ref for r in results}
    blocked = {
        i.key
        for i in (await session.execute(select(Issue).where(Issue.status == "blocked")))
        .scalars()
        .all()
    }
    assert keys <= blocked


async def test_slack_search_finds_incident_cause(session) -> None:
    results = await search_slack(session, "backfill connection pool saturated")
    assert results and results[0].source_type == SourceType.SLACK
    assert "pool" in results[0].snippet.lower()


async def test_commit_search_with_service_filter(session) -> None:
    results = await search_commits(session, "backfill", service="data-pipeline")
    assert any(r.source_ref == "b2c3d4e" for r in results)
    assert all(r.metadata.get("service") == "data-pipeline" for r in results)
