"""v1 scoring heuristics.

The brief shows a single 0-100 "신규성·관련도" score per item. True novelty
(patent-family size, forward/backward citations, claim breadth) is a v2
deep-dive concern — see the spec backlog. v1 therefore uses transparent,
cheap proxies and labels them as such:

* **Relevance** is what we can compute now: for lens A, how squarely the doc
  sits in automotive art; for lens B, the semantic similarity to the problem.
* **Recency** nudges fresher publications up within the weekly window.

Everything returns an ``int`` in [0, 100].
"""

from __future__ import annotations

import re

from .config import DateWindow
from .models import Patent
from .registry import LENS_A_CPC_PREFIX, Problem


def _clamp(x: float) -> int:
    return max(0, min(100, round(x)))


def _recency_bonus(patent: Patent, window: DateWindow) -> float:
    """0 at the start of the window, ~1.0 at the end."""
    span = max(1, window.end_int - window.start_int)
    # publication_date is yyyymmdd; treating the int delta as ordinal is a
    # coarse but monotonic proxy within a 7-day window.
    pos = (patent.publication_date - window.start_int) / span
    return max(0.0, min(1.0, pos))


def score_lens_a(patent: Patent, window: DateWindow) -> int:
    """Lens A: deterministic hit, so score = automotive density + recency."""
    cpc_hits = sum(
        1 for code in patent.cpc_codes
        for pre in LENS_A_CPC_PREFIX if code.startswith(pre)
    )
    # diminishing returns: 1 hit ~ 60, 2 ~ 75, 3+ ~ 85, then recency tops it up.
    density = 100 * (1 - 0.5 ** cpc_hits) if cpc_hits else 40
    return _clamp(0.85 * density + 15 * _recency_bonus(patent, window))


def score_lens_b(similarity: float, patent: Patent, problem: Problem,
                 window: DateWindow) -> int:
    """Lens B: similarity-dominated, with a small multi-CPC and recency lift."""
    cpc_hits = sum(
        1 for code in patent.cpc_codes
        for pre in problem.cpc_prefixes if code.startswith(pre)
    )
    base = 100 * max(0.0, min(1.0, similarity))
    cpc_lift = min(8.0, 4.0 * (cpc_hits - 1)) if cpc_hits > 1 else 0.0
    return _clamp(0.88 * base + cpc_lift + 6 * _recency_bonus(patent, window))


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def one_liner(patent: Patent, max_len: int = 140) -> str:
    """First sentence of the abstract, collapsed and trimmed."""
    text = " ".join((patent.abstract or patent.title or "").split())
    if not text:
        return patent.title or "(no abstract)"
    first = _SENT_SPLIT.split(text, maxsplit=1)[0]
    if len(first) > max_len:
        first = first[: max_len - 1].rstrip() + "…"
    return first
