"""Source abstraction so lenses don't depend on BigQuery directly.

The real implementation lives in ``bigquery_source.py``. ``FakePatentSource``
lets the lenses, scoring and brief be tested end-to-end with no credentials.
"""

from __future__ import annotations

from typing import Protocol, Sequence

from .config import DateWindow
from .models import Patent
from .registry import Competitor, Problem


class PatentSource(Protocol):
    def lens_a_patents(self, competitors: Sequence[Competitor],
                       window: DateWindow) -> list[Patent]:
        """Newly published docs assigned to any of ``competitors``."""
        ...

    def lens_b_candidates(self, problem: Problem, window: DateWindow,
                          limit: int) -> list[Patent]:
        """CPC-prefiltered candidate docs for one problem (pre-ranking)."""
        ...


class FakePatentSource:
    """In-memory source for tests and dry local runs.

    Returns documents from a fixed pool, applying the same assignee/CPC
    filtering semantics as the real source so the lenses behave identically.
    """

    def __init__(self, pool: Sequence[Patent]):
        self.pool = list(pool)

    def lens_a_patents(self, competitors, window):
        aliases = [(c, a.lower()) for c in competitors for a in c.aliases]
        out: list[Patent] = []
        for p in self.pool:
            if not (window.start_int <= p.publication_date <= window.end_int):
                continue
            joined = " | ".join(p.assignees).lower()
            if any(alias in joined for _, alias in aliases):
                out.append(p)
        return out

    def lens_b_candidates(self, problem, window, limit):
        out: list[Patent] = []
        for p in self.pool:
            if not (window.start_int <= p.publication_date <= window.end_int):
                continue
            if not p.abstract:
                continue
            if any(code.startswith(pre) for code in p.cpc_codes
                   for pre in problem.cpc_prefixes):
                out.append(p)
        return out[:limit]
