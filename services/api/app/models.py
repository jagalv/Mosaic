"""ORM models for Milestone 1: companies, filings, and tall financial facts.

`financials` is intentionally tall (one row per line-item/year); the company
page pivots it to a wide table at query time. CIK is the natural key for a
company and is stored as a plain integer (zero-padded only when building EDGAR
URLs).
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Company(Base):
    __tablename__ = "companies"

    cik: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    ticker: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # sector is approximate (derived from SIC); industry is the SEC sicDescription.
    sector: Mapped[str | None] = mapped_column(String)
    industry: Mapped[str | None] = mapped_column(String)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Filing(Base):
    __tablename__ = "filings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cik: Mapped[int] = mapped_column(
        ForeignKey("companies.cik"), nullable=False, index=True
    )
    accession_no: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    form_type: Mapped[str] = mapped_column(String, nullable=False)
    filing_date: Mapped[date | None] = mapped_column(Date)
    period_of_report: Mapped[date | None] = mapped_column(Date)
    primary_doc_url: Mapped[str | None] = mapped_column(String)


class Financial(Base):
    __tablename__ = "financials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cik: Mapped[int] = mapped_column(
        ForeignKey("companies.cik"), nullable=False, index=True
    )
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_period: Mapped[str] = mapped_column(String, nullable=False)  # 'FY' for now
    statement_type: Mapped[str] = mapped_column(String, nullable=False)
    concept: Mapped[str] = mapped_column(String, nullable=False)  # winning us-gaap tag
    line_item: Mapped[str] = mapped_column(String, nullable=False)  # our clean name
    value: Mapped[Decimal] = mapped_column(Numeric, nullable=False)  # exact, actual $
    unit: Mapped[str] = mapped_column(String, nullable=False)
    source_accession: Mapped[str | None] = mapped_column(String)
    # The fact's own `filed` date (from companyfacts) — for auditability.
    filed_date: Mapped[date | None] = mapped_column(Date)

    __table_args__ = (
        UniqueConstraint(
            "cik",
            "line_item",
            "fiscal_year",
            "fiscal_period",
            name="uq_financials_cik_line_year_period",
        ),
        Index("ix_financials_cik_statement", "cik", "statement_type"),
    )


class FilingDocument(Base):
    """Cleaned plain text of a filing's primary document (1:1 with a filing).

    `content_text` is immutable once written: section char offsets index into
    it, and Milestone 3 citations depend on those offsets staying stable. It is
    only re-derived on an explicit --refresh, which re-segments in the same pass.
    """

    __tablename__ = "filing_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filing_id: Mapped[int] = mapped_column(
        ForeignKey("filings.id"), unique=True, nullable=False
    )
    source_url: Mapped[str | None] = mapped_column(String)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    char_length: Mapped[int] = mapped_column(Integer, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FilingSection(Base):
    """A structural section of a filing (e.g. Item 1A Risk Factors).

    char_start/char_end are half-open offsets into the 1:1
    FilingDocument.content_text.
    """

    __tablename__ = "filing_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filing_id: Mapped[int] = mapped_column(
        ForeignKey("filings.id"), nullable=False, index=True
    )
    section_code: Mapped[str] = mapped_column(String, nullable=False)  # e.g. 'item1a'
    title: Mapped[str] = mapped_column(String, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("filing_id", "section_code", name="uq_sections_filing_code"),
    )
