"""companies, filings, financials

Milestone 1: core schema for SEC ingestion. `financials` is tall (one row per
line-item/year); the company page pivots it at query time.

NOTE: autogenerate wanted to drop `health_check` (it's created by raw SQL in
0001, not an ORM model). That drop was removed by hand — health_check stays.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("cik", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("sector", sa.String(), nullable=True),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("cik"),
    )
    op.create_index(
        op.f("ix_companies_ticker"), "companies", ["ticker"], unique=True
    )

    op.create_table(
        "filings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cik", sa.Integer(), nullable=False),
        sa.Column("accession_no", sa.String(), nullable=False),
        sa.Column("form_type", sa.String(), nullable=False),
        sa.Column("filing_date", sa.Date(), nullable=True),
        sa.Column("period_of_report", sa.Date(), nullable=True),
        sa.Column("primary_doc_url", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["cik"], ["companies.cik"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("accession_no"),
    )
    op.create_index(op.f("ix_filings_cik"), "filings", ["cik"], unique=False)

    op.create_table(
        "financials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cik", sa.Integer(), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("fiscal_period", sa.String(), nullable=False),
        sa.Column("statement_type", sa.String(), nullable=False),
        sa.Column("concept", sa.String(), nullable=False),
        sa.Column("line_item", sa.String(), nullable=False),
        sa.Column("value", sa.Numeric(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("source_accession", sa.String(), nullable=True),
        sa.Column("filed_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["cik"], ["companies.cik"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "cik",
            "line_item",
            "fiscal_year",
            "fiscal_period",
            name="uq_financials_cik_line_year_period",
        ),
    )
    op.create_index(op.f("ix_financials_cik"), "financials", ["cik"], unique=False)
    op.create_index(
        "ix_financials_cik_statement",
        "financials",
        ["cik", "statement_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_financials_cik_statement", table_name="financials")
    op.drop_index(op.f("ix_financials_cik"), table_name="financials")
    op.drop_table("financials")
    op.drop_index(op.f("ix_filings_cik"), table_name="filings")
    op.drop_table("filings")
    op.drop_index(op.f("ix_companies_ticker"), table_name="companies")
    op.drop_table("companies")
