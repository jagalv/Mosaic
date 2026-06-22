"""watchlists + watchlist_items with row-level security (Milestone 4b)

Both tables get RLS ENABLED *and* FORCED — the app connects as the table owner
(`mosaic`), and owners BYPASS RLS unless FORCE is set, so without FORCE the
policies would do nothing. Policies key on the per-request GUC
`app.current_user_id` (set via set_config(..., is_local => true) inside the
request transaction). NULLIF(...,'')::int makes an unset/empty GUC match NO rows
(fail-closed) instead of erroring.

Hand-written; raw SQL for the RLS DDL (op.* can't express it), op.* for tables.

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_UID = "NULLIF(current_setting('app.current_user_id', true), '')::int"


def upgrade() -> None:
    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_watchlists_user_id"), "watchlists", ["user_id"])

    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("watchlist_id", sa.Integer(), nullable=False),
        sa.Column("company_cik", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["watchlist_id"], ["watchlists.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["company_cik"], ["companies.cik"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "watchlist_id", "company_cik", name="uq_watchlist_company"
        ),
    )
    op.create_index(
        op.f("ix_watchlist_items_watchlist_id"),
        "watchlist_items",
        ["watchlist_id"],
    )

    # --- Row-level security (the security core) ---
    op.execute("ALTER TABLE watchlists ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE watchlists FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY watchlists_owner ON watchlists
          USING (user_id = {_UID})
          WITH CHECK (user_id = {_UID})
        """
    )

    op.execute("ALTER TABLE watchlist_items ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE watchlist_items FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY watchlist_items_owner ON watchlist_items
          USING (
            watchlist_id IN (SELECT id FROM watchlists WHERE user_id = {_UID})
          )
          WITH CHECK (
            watchlist_id IN (SELECT id FROM watchlists WHERE user_id = {_UID})
          )
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS watchlist_items_owner ON watchlist_items")
    op.execute("DROP POLICY IF EXISTS watchlists_owner ON watchlists")
    op.drop_index(
        op.f("ix_watchlist_items_watchlist_id"), table_name="watchlist_items"
    )
    op.drop_table("watchlist_items")
    op.drop_index(op.f("ix_watchlists_user_id"), table_name="watchlists")
    op.drop_table("watchlists")
