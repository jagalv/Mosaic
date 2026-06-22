"""notes with row-level security (Milestone 4c)

A note attaches to EXACTLY ONE target — a company (company_cik) or a filing
(filing_id → filings.id, the filings PK) — enforced by a CHECK. RLS is per-table
and never inherited, so notes gets its own ENABLE + FORCE + owner policy, keyed
on the per-request GUC `app.current_user_id`, exactly like watchlists (0007).
NULLIF(...,'')::int makes an unset/empty GUC match no rows (fail-closed).

mosaic_app's CRUD grant comes from 0008's ALTER DEFAULT PRIVILEGES (this table
is created by the admin role after that), so no GRANT is needed here.

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_UID = "NULLIF(current_setting('app.current_user_id', true), '')::int"


def upgrade() -> None:
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("company_cik", sa.Integer(), nullable=True),
        sa.Column("filing_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_cik"], ["companies.cik"]),
        sa.ForeignKeyConstraint(["filing_id"], ["filings.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "(company_cik IS NOT NULL)::int + (filing_id IS NOT NULL)::int = 1",
            name="ck_notes_one_target",
        ),
    )
    op.create_index(op.f("ix_notes_user_id"), "notes", ["user_id"])
    op.create_index(op.f("ix_notes_company_cik"), "notes", ["company_cik"])
    op.create_index(op.f("ix_notes_filing_id"), "notes", ["filing_id"])

    # --- Row-level security (per-table; not inherited) ---
    op.execute("ALTER TABLE notes ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE notes FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY notes_owner ON notes
          USING (user_id = {_UID})
          WITH CHECK (user_id = {_UID})
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS notes_owner ON notes")
    op.drop_index(op.f("ix_notes_filing_id"), table_name="notes")
    op.drop_index(op.f("ix_notes_company_cik"), table_name="notes")
    op.drop_index(op.f("ix_notes_user_id"), table_name="notes")
    op.drop_table("notes")
