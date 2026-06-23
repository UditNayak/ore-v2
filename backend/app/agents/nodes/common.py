"""Shared helpers for graph nodes: per-request context and tool dispatch (DRY)."""

from collections.abc import Awaitable, Callable

from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import SourceType
from app.llm.gateway import LLMGateway
from app.tools import search_commits, search_docs, search_issues, search_slack
from app.tools.schemas import Evidence

# Tools the Investigator can dispatch, keyed by source type. (LEARNING is not searchable here.)
ToolFn = Callable[[AsyncSession, str], Awaitable[list[Evidence]]]
TOOLS: dict[SourceType, ToolFn] = {
    SourceType.DOC: search_docs,
    SourceType.ISSUE: search_issues,
    SourceType.SLACK: search_slack,
    SourceType.COMMIT: search_commits,
}
SEARCHABLE_SOURCES: list[str] = [s.value for s in TOOLS]


def context(config: RunnableConfig) -> tuple[AsyncSession, LLMGateway]:
    """Pull the request-scoped DB session and LLM gateway out of the runnable config."""
    cfg = (config or {}).get("configurable", {})
    return cfg["session"], cfg["gateway"]


async def run_tool(session: AsyncSession, source: str, query: str) -> list[Evidence]:
    """Dispatch a search to the tool for `source` (no-op for unknown/unsearchable sources)."""
    try:
        fn = TOOLS[SourceType(source)]
    except (KeyError, ValueError):
        return []
    return await fn(session, query)


def dedup_evidence(evidence: list[Evidence]) -> list[Evidence]:
    """Collapse duplicate (source_type, source_ref) hits, keeping the highest score."""
    best: dict[tuple[str, str], Evidence] = {}
    for e in evidence:
        key = (e.source_type, e.source_ref)
        if key not in best or (e.score or 0.0) > (best[key].score or 0.0):
            best[key] = e
    return list(best.values())


def format_evidence(evidence: list[Evidence]) -> str:
    """Compact, citable rendering of evidence for prompts."""
    if not evidence:
        return "(no evidence gathered yet)"
    return "\n".join(f"- [{e.source_type}:{e.source_ref}] {e.snippet[:220]}" for e in evidence)
