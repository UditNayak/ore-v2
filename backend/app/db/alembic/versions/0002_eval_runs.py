"""eval_runs table for evaluation-harness results

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-24

Creates only the eval_runs table (the model is registered on Base.metadata; we create
just this table to avoid touching existing ones). See docs/EVALUATION.md.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "eval_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("summary", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("results", postgresql.JSONB, nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_table("eval_runs")
