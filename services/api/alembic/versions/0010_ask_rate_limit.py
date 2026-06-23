"""ask_rate_limit — per-IP + global daily counters for the public /ask endpoint

The public "Ask this filing" endpoint runs on a SHARED Gemini free tier (~20
requests/day on ONE key, across all visitors). This table counts REAL Gemini
calls per UTC day, keyed by a client-ip hash AND by a global sentinel row
('GLOBAL'), so the API can switch to demo-mode DETERMINISTICALLY before the
provider starts returning 429s. DB-backed (not in-memory) so the counts survive
a Hugging Face Space restart/sleep.

NO row-level security: this is anonymous infrastructure data (like answer_cache
and ai_interactions), NOT user-owned rows — so no ENABLE/FORCE RLS and no owner
policy. mosaic_app's CRUD comes from 0008's ALTER DEFAULT PRIVILEGES (this table
is created by the admin role after 0008, so it's covered automatically). The
composite PK means there is no sequence to grant either.

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ask_rate_limit",
        sa.Column("ip_hash", sa.Text(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("ip_hash", "day", name="pk_ask_rate_limit"),
    )


def downgrade() -> None:
    op.drop_table("ask_rate_limit")
