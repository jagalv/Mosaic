"""Segmentation golden test — pins 10-K Item detection against a real filing.

The fixture (tests/fixtures/aapl_10k_fy2023.txt) is the actual cleaned text of
Apple's FY2023 10-K (accession 0000320193-23-000106). Expectations below were
confirmed against that real filing, not memory. Offline + deterministic.
"""

from pathlib import Path

from app.ingest.sections import html_to_text, segment_10k

FIXTURE = Path(__file__).parent / "fixtures" / "aapl_10k_fy2023.txt"
TEXT = FIXTURE.read_text(encoding="utf-8")


def _by_code():
    return {s.section_code: s for s in segment_10k(TEXT)}


def test_item_1a_risk_factors_present_and_substantial():
    secs = _by_code()
    assert "item1a" in secs
    ia = secs["item1a"]
    assert ia.title == "Item 1A. Risk Factors"
    # Real section is ~67,892 chars; pin "non-trivially long" with margin.
    assert ia.char_end - ia.char_start > 20_000
    body = TEXT[ia.char_start : ia.char_end]
    assert body.lstrip().startswith("Item 1A")
    assert "Risk Factors" in body and "macroeconomic" in body


def test_item_7_mdna_present():
    secs = _by_code()
    assert "item7" in secs
    mdna = secs["item7"]
    assert mdna.title.startswith("Item 7. Management")
    assert mdna.char_end - mdna.char_start > 5_000  # real ~15,511


def test_sections_ordered_and_non_overlapping():
    secs = segment_10k(TEXT)
    assert secs, "expected sections"
    for i in range(len(secs) - 1):
        assert secs[i].char_start < secs[i].char_end <= secs[i + 1].char_start


def test_table_of_contents_not_mistaken_for_body():
    # The first real section is Item 1 (Business); if TOC entries leaked in, an
    # out-of-order/earlier item would appear first.
    secs = segment_10k(TEXT)
    assert secs[0].section_code == "item1"


def test_html_to_text_strips_tags_and_normalizes():
    html = (
        "<html><body>"
        "<script>var x=1;</script><style>.a{}</style>"
        "<div>Item 1. Business</div>"
        "<p>Hello&nbsp;&nbsp;world</p>"
        "</body></html>"
    )
    out = html_to_text(html)
    assert "var x=1" not in out and ".a{}" not in out
    assert "Item 1. Business" in out
    assert "Hello world" in out  # nbsp -> space, runs collapsed
