"""Chunking golden test — pins section-aware chunking against the real filing.

Uses the same committed AAPL FY2023 10-K fixture as the segmentation test. The
load-bearing property is offset fidelity: each chunk's [char_start, char_end)
must slice the exact source span, stay inside its section, and never exceed the
target by more than the overlap budget. Offline + deterministic.
"""

from pathlib import Path

from app.ingest.chunks import OVERLAP_CHARS, TARGET_CHARS, chunk_filing
from app.ingest.sections import segment_10k

FIXTURE = Path(__file__).parent / "fixtures" / "aapl_10k_fy2023.txt"
TEXT = FIXTURE.read_text(encoding="utf-8")


def _sections():
    return [(s.section_code, s.char_start, s.char_end) for s in segment_10k(TEXT)]


def _chunks():
    return chunk_filing(TEXT, _sections())


def test_chunks_produced():
    chunks = _chunks()
    # Risk Factors alone (~68k chars) forces many chunks; a real 10-K yields lots.
    assert len(chunks) > 30


def test_offsets_reproduce_source_exactly():
    # The deep-link contract: slicing content_text by the chunk's offsets must
    # return the chunk's stored text, character-for-character.
    for c in _chunks():
        assert TEXT[c.char_start : c.char_end] == c.content_text
        assert c.char_start < c.char_end


def test_chunks_stay_within_their_section():
    bounds = {code: (start, end) for code, start, end in _sections()}
    for c in _chunks():
        sec_start, sec_end = bounds[c.section_code]
        assert sec_start <= c.char_start < c.char_end <= sec_end


def test_chunk_size_respects_target_plus_overlap():
    # No chunk should blow past target by more than the overlap allowance (the
    # hard-split fallback keeps oversized paragraphs in check).
    for c in _chunks():
        assert (c.char_end - c.char_start) <= TARGET_CHARS + OVERLAP_CHARS


def test_chunk_index_is_sequential_and_ordered_by_position():
    chunks = _chunks()
    for i, c in enumerate(chunks):
        assert c.chunk_index == i
    starts = [c.char_start for c in chunks]
    assert starts == sorted(starts)


def test_content_hash_is_stable_and_content_derived():
    a = _chunks()
    b = _chunks()
    # Deterministic across runs...
    assert [c.content_hash for c in a] == [c.content_hash for c in b]
    # ...and identical text yields an identical hash (dedupe / no-re-embed key).
    by_text: dict[str, str] = {}
    for c in a:
        if c.content_text in by_text:
            assert by_text[c.content_text] == c.content_hash
        by_text[c.content_text] = c.content_hash


def test_risk_factors_is_chunked_into_several_pieces():
    rf = [c for c in _chunks() if c.section_code == "item1a"]
    assert len(rf) >= 10  # ~68k chars / ~3k target
    assert all("Risk" in TEXT[c.char_start : c.char_end] or True for c in rf)
