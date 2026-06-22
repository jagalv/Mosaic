"""ORM models for Milestone 1: companies, filings, and tall financial facts.

`financials` is intentionally tall (one row per line-item/year); the company
page pivots it to a wide table at query time. CIK is the natural key for a
company and is stored as a plain integer (zero-padded only when building EDGAR
URLs).
"""

from datetime import date, datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

# Embedding dimension for BAAI/bge-small-en-v1.5. Locked at migration 0004;
# changing this requires a re-embed + a new migration (see DECISIONS).
EMBEDDING_DIM = 384


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


class FilingChunk(Base):
    """A retrieval chunk: a sub-span of a section's text, with its embedding.

    char_start/char_end are absolute half-open offsets into the 1:1
    FilingDocument.content_text (NOT relative to the section) so a citation can
    deep-link straight into the reader. content_hash is the sha256 of
    content_text: unchanged chunks keep the same hash and are never re-embedded.
    `embedding` is nullable so chunking (Slice A) can land before embedding
    (Slice B). `tsv` is a Postgres GENERATED tsvector column (maintained by the
    DB, not the app) backing the keyword half of hybrid retrieval.
    """

    __tablename__ = "filing_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filing_id: Mapped[int] = mapped_column(
        ForeignKey("filings.id"), nullable=False, index=True
    )
    section_code: Mapped[str] = mapped_column(String, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String, nullable=False, index=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))

    __table_args__ = (
        UniqueConstraint(
            "filing_id", "chunk_index", name="uq_chunks_filing_index"
        ),
    )


class AiInteraction(Base):
    """Audit log of one Ask-this-filing call: prompt, what was retrieved, cost.

    Written on every answered request (cache hits included, flagged via
    `cached`) so retrieval quality and latency/tokens stay observable.
    """

    __tablename__ = "ai_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    filing_id: Mapped[int | None] = mapped_column(
        ForeignKey("filings.id"), index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text)
    retrieved_chunk_ids: Mapped[list | None] = mapped_column(JSON)
    provider: Mapped[str | None] = mapped_column(String)
    model: Mapped[str | None] = mapped_column(String)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    abstained: Mapped[bool | None] = mapped_column(Boolean)
    # Numbers-guard result: figures in the answer not found in retrieved text.
    unsupported_numbers: Mapped[list | None] = mapped_column(JSON)
    cached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    feedback: Mapped[str | None] = mapped_column(String)


class AnswerCache(Base):
    """Cached answer for a repeated question on a filing.

    The cache key includes provider + model (James's call): swapping LLM_MODEL
    must never serve a stale answer generated by a different model.
    """

    __tablename__ = "answer_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filing_id: Mapped[int] = mapped_column(
        ForeignKey("filings.id"), nullable=False, index=True
    )
    question_hash: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_chunk_ids: Mapped[list | None] = mapped_column(JSON)
    abstained: Mapped[bool | None] = mapped_column(Boolean)
    # Numbers-guard result, persisted so a cache hit warns identically to a fresh
    # answer.
    unsupported_numbers: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "filing_id",
            "question_hash",
            "provider",
            "model",
            name="uq_answer_cache_key",
        ),
    )


class User(Base):
    """An application user (Milestone 4a auth).

    `email` is stored lower-cased and is unique (case-insensitive identity without
    needing the Postgres citext extension). `password_hash` is an argon2 hash —
    never a plaintext or reversible value.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Watchlist(Base):
    """A user's named watchlist (Milestone 4b). Row-level security restricts
    every read/write to the owning user (enforced in the DB — migration 0007)."""

    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class WatchlistItem(Base):
    """A company in a watchlist. `company_cik` references companies.cik (the
    Company PK). RLS scopes items via their parent watchlist's owner."""

    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    watchlist_id: Mapped[int] = mapped_column(
        ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_cik: Mapped[int] = mapped_column(
        ForeignKey("companies.cik"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "watchlist_id", "company_cik", name="uq_watchlist_company"
        ),
    )


class Note(Base):
    """A user's note, attached to EXACTLY ONE target — a company or a filing
    (Milestone 4c). RLS restricts every read/write to the owning user (the same
    enforced-in-DB pattern as watchlists; migration 0009)."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # Exactly one of these is non-null (enforced by ck_notes_one_target).
    company_cik: Mapped[int | None] = mapped_column(
        ForeignKey("companies.cik"), index=True
    )
    filing_id: Mapped[int | None] = mapped_column(
        ForeignKey("filings.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "(company_cik IS NOT NULL)::int + (filing_id IS NOT NULL)::int = 1",
            name="ck_notes_one_target",
        ),
    )
