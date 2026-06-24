"""add expected_sources to human_answers

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-24

Lets the expert declare which sources they used, so evidence coverage can be scored for
ad-hoc (UI-submitted) questions. See docs/EVALUATION.md.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "human_answers",
        sa.Column("expected_sources", postgresql.JSONB, nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("human_answers", "expected_sources")
