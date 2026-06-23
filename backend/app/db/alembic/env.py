"""Alembic environment. Runs migrations synchronously using a sync (psycopg) DSN
derived from the application's async DATABASE_URL.
"""

import app.db.models  # noqa: F401 — register all models on Base.metadata
from alembic import context
from app.core.config import get_settings
from app.db.base import Base
from sqlalchemy import create_engine

target_metadata = Base.metadata


def _sync_url() -> str:
    """Convert the app's async DSN to a sync one for Alembic (asyncpg -> psycopg)."""
    return get_settings().database_url.replace("+asyncpg", "+psycopg")


def run_migrations_online() -> None:
    engine = create_engine(_sync_url())
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


def run_migrations_offline() -> None:
    context.configure(url=_sync_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
