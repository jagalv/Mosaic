"""Filing HTML -> clean text + structural sections.

This is the milestone's hard part. Two steps, kept separate so each is testable:

  html_to_text(html)  -> canonical plain text (offsets index into THIS string)
  segment_10k(text)   -> [Section] with half-open [char_start, char_end) offsets

10-K Item numbers are unique across the document (Part I: 1-4, II: 5-9,
III: 10-14, IV: 15), so no Part disambiguation is needed. 10-Q repeats Item
numbers across Parts and is intentionally NOT segmented here (text is stored,
sections deferred) — see DECISIONS.

Known fragility (documented, not hidden):
  - The table of contents repeats every Item heading near the top. TOC entries
    wrap the title onto the next line, so the heading line itself has no
    same-line title; we require a non-empty same-line title, which drops the
    whole TOC and keeps the body headings. As a backstop we also take the LAST
    occurrence per code.
  - Line-anchored matching plus a length cap means mid-paragraph
    "...see Item 1A..." cross-references don't masquerade as section starts.
  - A filer that wraps a real body heading's title onto the next line, or splits
    heading words across inline tags with no spaces, can still slip through. Our
    10 large-cap filers are conventional; this is not claimed to be universal.
"""

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

# Tags whose boundaries should become newlines so headings land on their own line.
_BLOCK_TAGS = [
    "p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "ul", "ol", "section",
]

# Line-anchored Item heading: "Item 1A. Risk Factors", "ITEM 7 — MD&A", etc.
_HEADING_RE = re.compile(
    r"(?im)^item\s+(\d{1,2})([a-c])?\b[ \t]*[\.\:\-–—]?[ \t]*(.*)$"
)
# Real Item headings are a single line; a generous cap excludes body paragraphs
# that happen to begin with "Item N" while still admitting long titles like
# "Item 7. Management's Discussion and Analysis ..." (~92 chars).
_MAX_HEADING_LEN = 200

# Canonical titles for stability; falls back to the filer's detected text.
_CANONICAL_TITLES: dict[str, str] = {
    "item1": "Item 1. Business",
    "item1a": "Item 1A. Risk Factors",
    "item1b": "Item 1B. Unresolved Staff Comments",
    "item1c": "Item 1C. Cybersecurity",
    "item2": "Item 2. Properties",
    "item3": "Item 3. Legal Proceedings",
    "item4": "Item 4. Mine Safety Disclosures",
    "item5": "Item 5. Market for Registrant's Common Equity",
    "item6": "Item 6. Selected Financial Data",
    "item7": "Item 7. Management's Discussion and Analysis",
    "item7a": "Item 7A. Quantitative and Qualitative Disclosures About Market Risk",
    "item8": "Item 8. Financial Statements and Supplementary Data",
    "item9": "Item 9. Changes in and Disagreements with Accountants",
    "item9a": "Item 9A. Controls and Procedures",
    "item9b": "Item 9B. Other Information",
    "item10": "Item 10. Directors, Executive Officers and Corporate Governance",
    "item11": "Item 11. Executive Compensation",
    "item12": "Item 12. Security Ownership of Certain Beneficial Owners",
    "item13": "Item 13. Certain Relationships and Related Transactions",
    "item14": "Item 14. Principal Accountant Fees and Services",
    "item15": "Item 15. Exhibits and Financial Statement Schedules",
}


@dataclass(frozen=True)
class Section:
    section_code: str
    title: str
    order_index: int
    char_start: int
    char_end: int


def html_to_text(html: str) -> str:
    """Strip a filing's HTML to canonical, readable plain text."""
    soup = BeautifulSoup(html, "html.parser")

    # Drop non-content: scripts/styles and the inline-XBRL hidden header.
    for tag in soup(["script", "style", "ix:header", "ix:hidden"]):
        tag.decompose()
    # Drop explicitly hidden nodes (some filers tuck XBRL facts in display:none).
    for tag in soup.find_all(
        style=lambda s: bool(s) and "display:none" in s.replace(" ", "").lower()
    ):
        tag.decompose()

    # Force a newline at block boundaries; inline runs (spans) stay joined.
    for tag in soup.find_all(_BLOCK_TAGS):
        tag.insert_after("\n")

    raw = soup.get_text(separator=" ").replace("\xa0", " ")

    # Normalize: collapse intra-line whitespace, trim lines, cap blank runs.
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in raw.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _canonical_title(code: str, detected: str) -> str:
    if code in _CANONICAL_TITLES:
        return _CANONICAL_TITLES[code]
    detected = detected.strip(" .:-–—")
    label = code.replace("item", "Item ").upper().replace("ITEM ", "Item ")
    return f"{label}. {detected}" if detected else label


def segment_10k(text: str) -> list[Section]:
    """Segment 10-K clean text into Item sections by structural headings."""
    # Collect candidate body headings: a single line "Item N[letter]. <title>"
    # with a non-empty same-line title (this drops the title-wrapped TOC).
    candidates: list[tuple[str, int, str]] = []  # (code, start, detected_title)
    for m in _HEADING_RE.finditer(text):
        line = text[m.start() : m.end()]
        if len(line) > _MAX_HEADING_LEN:
            continue
        num, letter, detected = m.group(1), m.group(2), m.group(3)
        if not detected.strip():
            continue  # title wrapped to next line -> table-of-contents entry
        code = f"item{num}{(letter or '').lower()}"
        candidates.append((code, m.start(), detected))

    # Keep the LAST occurrence of each code (body, not table of contents).
    last_by_code: dict[str, tuple[int, str]] = {}
    for code, start, detected in candidates:
        last_by_code[code] = (start, detected)

    ordered = sorted(
        ((start, code, detected) for code, (start, detected) in last_by_code.items()),
        key=lambda x: x[0],
    )

    sections: list[Section] = []
    for i, (start, code, detected) in enumerate(ordered):
        end = ordered[i + 1][0] if i + 1 < len(ordered) else len(text)
        sections.append(
            Section(
                section_code=code,
                title=_canonical_title(code, detected),
                order_index=i,
                char_start=start,
                char_end=end,
            )
        )
    return sections


def segment_filing(html: str, form_type: str) -> tuple[str, list[Section]]:
    """Clean a filing and segment it. Only 10-K forms are segmented (M2 scope)."""
    text = html_to_text(html)
    sections = segment_10k(text) if form_type in ("10-K", "10-K/A") else []
    return text, sections
