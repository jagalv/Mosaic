"""Filing reader endpoint: returns a filing's cleaned text + sections.

The frontend slices `content_text` by each section's [char_start, char_end)
to render navigable sections. 404 if the filing or its document isn't ingested.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Company, Filing, FilingDocument, FilingSection

router = APIRouter()


@router.get("/filing/{accession_no}")
def get_filing(accession_no: str, db: Session = Depends(get_session)) -> dict:
    filing = db.scalar(select(Filing).where(Filing.accession_no == accession_no))
    if filing is None:
        raise HTTPException(status_code=404, detail=f"Filing {accession_no} not found")

    doc = db.scalar(
        select(FilingDocument).where(FilingDocument.filing_id == filing.id)
    )
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"Filing {accession_no} has no ingested document",
        )

    company = db.scalar(select(Company).where(Company.cik == filing.cik))
    sections = db.scalars(
        select(FilingSection)
        .where(FilingSection.filing_id == filing.id)
        .order_by(FilingSection.order_index)
    ).all()

    return {
        "accession_no": filing.accession_no,
        "form_type": filing.form_type,
        "filing_date": filing.filing_date.isoformat() if filing.filing_date else None,
        "period_of_report": (
            filing.period_of_report.isoformat() if filing.period_of_report else None
        ),
        "primary_doc_url": filing.primary_doc_url,
        "company": {
            "ticker": company.ticker if company else None,
            "name": company.name if company else None,
        },
        "content_text": doc.content_text,
        "sections": [
            {
                "section_code": s.section_code,
                "title": s.title,
                "char_start": s.char_start,
                "char_end": s.char_end,
            }
            for s in sections
        ],
    }
