"""Shared fixtures. The `session` fixture guarantees a migrated + seeded database
(both operations are idempotent) and yields an async session against the compose `db`.

Each test gets a fresh NullPool engine bound to that test's event loop, then disposes it.
This avoids asyncpg connections being reused across (closed) per-test event loops.
"""

import asyncio
from collections.abc import AsyncIterator

import pytest_asyncio
from app.core.config import get_settings
from app.db.migrate import run_migrations
from app.db.seed import seed_if_empty
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    await asyncio.to_thread(run_migrations)
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as db:
        await seed_if_empty(db)
        yield db
    await engine.dispose()
