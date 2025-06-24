"""add ref slug to documents

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-27

Gives documents a human-readable slug (e.g. "doc-release-v2.4") so the source_ref shown in
evidence matches what the expert cites — making evidence coverage visually verifiable.
Nullable + unique; the seed populates it on (re)seed.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("ref", sa.Text(), nullable=True))
    op.create_unique_constraint("uq_documents_ref", "documents", ["ref"])


def downgrade() -> None:
    op.drop_constraint("uq_documents_ref", "documents", type_="unique")
    op.drop_column("documents", "ref")
