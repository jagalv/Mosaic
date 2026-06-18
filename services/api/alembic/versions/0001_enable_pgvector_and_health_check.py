"""enable pgvector and create health_check table

Milestone 0: proves migrations run end-to-end and that the pgvector extension
is available in our Postgres. The health_check table is deliberately trivial —
no product schema lives here yet.

Revision ID: 0001
Revises:
Create Date: 2026-06-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Requires the pgvector image (extension files preinstalled). Idempotent.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "health_check",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("health_check")
    # Leave the `vector` extension in place on downgrade — other objects may
    # depend on it and dropping an extension is rarely what you want.
