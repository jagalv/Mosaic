"""Numbers guard — the trust spine's last line of defense.

Mosaic exists because generic AI fabricates figures on filings. The grounding
prompt asks the model not to; this module *verifies* it in code: every
significant number in an answer must trace to the retrieved excerpts, or it is
reported as unsupported (the caller flags-and-warns — see answer.py).

Matching is by **digit-core**: drop everything but digits (so `$`, commas, `%`,
decimal points, and scale words like "million" fall away), then require the
answer number's core to be a substring of some excerpt number's core. That makes
`$383,285 million`, `383,285`, and `383285000000` all match a source `383,285`,
and tolerates rounding like `$391.0 billion` against `391,035`.

Deliberate scope / known limits (kept lightweight on purpose):
  - Only numbers with a **>=4-digit core** are checked. Small counts, 2-digit
    percentages, and the like collide spuriously and would flag good answers;
    the big financial figures are the high-value, low-collision target.
  - A *re-scaled* figure ("383.3 billion" derived from a "383,285 million"
    source) has core `3833`, which isn't in `383285`, so it won't match. Closing
    that needs unit-aware parsing of table headers — out of scope. This is why
    the policy is flag-and-warn, not silent withholding: a rare false positive
    must not destroy a correct answer.
"""

import re

# Smallest digit-core we bother checking. Below this, spurious collisions
# (page numbers, "16%", "Q3") would cause false positives.
MIN_CORE_DIGITS = 4

# A numeric token: optional leading $, digits with optional thousands commas and
# an optional decimal part, optional trailing %.
_NUMBER_RE = re.compile(r"\$?\d[\d,]*(?:\.\d+)?%?")
# Citation markers like [1] or [1, 2] are not figures — strip before scanning.
_CITATION_RE = re.compile(r"\[[\d,\s]+\]")


def _digit_core(token: str) -> str:
    return re.sub(r"\D", "", token)


def significant_number_cores(text: str) -> list[str]:
    """Digit-cores of every >=4-digit numeric token in `text` (order preserved)."""
    cleaned = _CITATION_RE.sub(" ", text)
    cores: list[str] = []
    for m in _NUMBER_RE.finditer(cleaned):
        core = _digit_core(m.group())
        if len(core) >= MIN_CORE_DIGITS:
            cores.append(core)
    return cores


def unsupported_numbers(answer: str, excerpt_text: str) -> list[str]:
    """Significant numbers in `answer` not traceable to `excerpt_text`.

    Returns the unique unsupported digit-cores, in the order they appear in the
    answer. Empty list == every figure is supported.
    """
    excerpt_cores = significant_number_cores(excerpt_text)
    unsupported: list[str] = []
    seen: set[str] = set()
    for core in significant_number_cores(answer):
        if core in seen:
            continue
        seen.add(core)
        if not any(core in ec for ec in excerpt_cores):
            unsupported.append(core)
    return unsupported
