"""initial schema: pgvector extension, all tables, vector indexes

Revision ID: 0001
Revises:
Create Date: 2026-06-24

The schema is defined once in app/db/models.py (DRY). This migration enables the
pgvector extension, materializes the models, and adds HNSW cosine indexes for the two
embedding columns. See docs/DB_SCHEMA.md.
"""

from collections.abc import Sequence

import app.db.models  # noqa: F401 — register models on Base.metadata
from alembic import op
from app.db.base import Base

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    Base.metadata.create_all(bind=bind)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding "
        "ON document_chunks USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_learning_events_embedding "
        "ON learning_events USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
