"""numbers-guard columns on ai_interactions and answer_cache

Milestone 3 close-out: persist the numbers-guard result (figures in an answer
not traceable to the retrieved text) so the audit log records guard trips and a
cache hit warns identically to a fresh answer.

Hand-written; adds two nullable JSON columns, touches nothing else.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ai_interactions",
        sa.Column("unsupported_numbers", sa.JSON(), nullable=True),
    )
    op.add_column(
        "answer_cache",
        sa.Column("unsupported_numbers", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("answer_cache", "unsupported_numbers")
    op.drop_column("ai_interactions", "unsupported_numbers")
