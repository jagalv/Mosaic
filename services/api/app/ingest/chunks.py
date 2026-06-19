"""Section-aware chunking for Milestone 3 RAG.

Turns a filing's immutable `content_text` + its `FilingSection` offsets into
retrieval chunks that carry ABSOLUTE char offsets back into that same text. The
offsets are the load-bearing contract: M3 citations deep-link into the original
filing by character range, so a chunk's [char_start, char_end) must slice the
exact source span (no cleaning, trimming, or re-derivation of the text here).

Strategy (decided with James): section-aware sub-chunks. Each section is packed,
on paragraph boundaries, into ~TARGET_CHARS windows with ~OVERLAP_CHARS of
overlap so a claim that straddles a window boundary is still retrievable whole.
A single paragraph larger than the target (rare: a flattened table, a giant risk
factor) is hard-split at whitespace as a fallback. Chunks never cross section
boundaries, so every chunk keeps a clean `section_code` for pre-filtering.

Plain text in, plain offsets out — no DB, no embeddings (that's embed.py). This
keeps the hard part testable against the committed AAPL fixture.
"""

import hashlib
import re
from dataclasses import dataclass

# Soft target / overlap in characters. ~3k chars is roughly 600-800 tokens for
# bge-small (512-token model): big enough to hold a coherent claim, small enough
# that retrieval stays precise and citations point at a tight span.
TARGET_CHARS = 3000
OVERLAP_CHARS = 400

# Paragraph = a maximal run of non-newline text (html_to_text already collapsed
# intra-line whitespace and capped blank runs).
_PARA_RE = re.compile(r"[^\n]+")


@dataclass(frozen=True)
class Chunk:
    section_code: str
    chunk_index: int  # 0-based, sequential within the filing (by char_start)
    char_start: int
    char_end: int
    content_text: str
    content_hash: str  # sha256 of content_text; identical text -> identical hash


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hard_split(
    text: str, start: int, end: int, target: int, overlap: int
) -> list[tuple[int, int]]:
    """Split one oversized span into overlapping windows, breaking at spaces."""
    spans: list[tuple[int, int]] = []
    pos = start
    while pos < end:
        win_end = min(pos + target, end)
        if win_end < end:
            # Prefer a space near the limit so we don't cut mid-word.
            sp = text.rfind(" ", pos + target - overlap, win_end)
            if sp > pos:
                win_end = sp
        spans.append((pos, win_end))
        if win_end >= end:
            break
        pos = max(win_end - overlap, pos + 1)
    return spans


def _chunk_section(
    text: str, sec_start: int, sec_end: int, target: int, overlap: int
) -> list[tuple[int, int]]:
    """Pack one section's paragraphs into overlapping [start, end) spans."""
    paras = [
        (sec_start + m.start(), sec_start + m.end())
        for m in _PARA_RE.finditer(text[sec_start:sec_end])
    ]
    if not paras:
        return []

    spans: list[tuple[int, int]] = []
    i = 0
    while i < len(paras):
        start = paras[i][0]
        # A single paragraph that already overflows the target -> hard-split it.
        if paras[i][1] - start > target:
            spans.extend(_hard_split(text, start, paras[i][1], target, overlap))
            i += 1
            continue

        # Grow the window paragraph-by-paragraph while it fits the target.
        j = i
        end = paras[i][1]
        while j + 1 < len(paras) and paras[j + 1][1] - start <= target:
            j += 1
            end = paras[j][1]
        spans.append((start, end))

        # Advance, re-including tail paragraphs within the overlap budget. The
        # max(i + 1, ...) guarantees forward progress (no infinite loop).
        next_i = j + 1
        for k in range(i + 1, j + 1):
            if paras[k][0] >= end - overlap:
                next_i = k
                break
        i = max(i + 1, next_i)
    return spans


def chunk_filing(
    text: str,
    sections: list[tuple[str, int, int]],
    target: int = TARGET_CHARS,
    overlap: int = OVERLAP_CHARS,
) -> list[Chunk]:
    """Chunk a filing.

    `sections` is [(section_code, char_start, char_end), ...] (the stored
    FilingSection offsets). Returns chunks ordered by char_start, each with
    absolute offsets into `text` and a sequential `chunk_index`.
    """
    raw: list[tuple[str, int, int]] = []  # (section_code, start, end)
    for section_code, sec_start, sec_end in sections:
        for start, end in _chunk_section(text, sec_start, sec_end, target, overlap):
            if end > start:
                raw.append((section_code, start, end))

    raw.sort(key=lambda r: r[1])
    return [
        Chunk(
            section_code=section_code,
            chunk_index=idx,
            char_start=start,
            char_end=end,
            content_text=text[start:end],
            content_hash=_content_hash(text[start:end]),
        )
        for idx, (section_code, start, end) in enumerate(raw)
    ]
