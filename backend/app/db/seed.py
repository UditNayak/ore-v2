"""Idempotent seeding of the synthetic knowledge corpus.

Loads the JSON datasets under the configured seed path, inserts issues / slack / commits,
and ingests documents (chunk + embed) into pgvector. Safe to call on every startup: it
no-ops if the corpus is already present.
"""

import json
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import Commit, Document, Issue, SlackMessage
from app.rag.ingest import ingest_document

log = structlog.get_logger("seed")


def _load(name: str) -> list[dict[str, Any]]:
    path = Path(get_settings().seed_path) / name
    data: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    return data


async def seed_if_empty(session: AsyncSession) -> bool:
    """Seed the corpus if it is empty. Returns True if seeding ran."""
    existing = await session.scalar(select(func.count()).select_from(Document))
    if existing:
        log.info("seed_skipped", reason="corpus already present", documents=existing)
        return False

    for row in _load("issues.json"):
        session.add(Issue(**row))
    for row in _load("slack.json"):
        session.add(SlackMessage(**row))
    for row in _load("commits.json"):
        session.add(Commit(**row))

    chunk_count = 0
    for row in _load("documents.json"):
        document = Document(**row)
        session.add(document)
        chunk_count += await ingest_document(session, document)

    await session.commit()
    log.info("seed_done", documents="loaded", chunks=chunk_count)
    return True


async def reseed(session: AsyncSession) -> None:
    """Wipe the knowledge corpus and re-seed it (for dev/data refreshes)."""
    for model in (Document, Issue, SlackMessage, Commit):
        await session.execute(delete(model))  # Document delete cascades to chunks
    await session.commit()
    await seed_if_empty(session)


if __name__ == "__main__":
    import asyncio
    import sys

    from app.db.session import SessionLocal

    force = "--force" in sys.argv

    async def _run() -> None:
        async with SessionLocal() as db:
            if force:
                await reseed(db)
            else:
                await seed_if_empty(db)

    asyncio.run(_run())
