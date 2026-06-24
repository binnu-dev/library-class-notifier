"""Lightweight free source: PatentsView PatentSearch API.

A zero-cost alternative to BigQuery for testing and small runs. Tradeoffs vs.
BigQuery (documented so nobody is surprised):

* Coverage: **granted US patents only** (not global publications).
* Freshness: the dataset refreshes **quarterly**, and ``patent_date`` is the
  *grant* date — so a 7-day window will usually be empty. Widen the lookback
  (e.g. ``--lookback-days 365``) when using this source.
* Cost/setup: free. Requires a free API key (no card), sent as ``X-Api-Key``.
  Get one at https://patentsview.org/apis (issued immediately).

The endpoint, fields and operators follow the v1 PatentSearch API:
https://search.patentsview.org/docs/
"""

from __future__ import annotations

from typing import Sequence

from .config import DateWindow
from .models import Patent
from .registry import Competitor, Problem

API_URL = "https://search.patentsview.org/api/v1/patent/"

_FIELDS = [
    "patent_id",
    "patent_title",
    "patent_abstract",
    "patent_date",
    "assignees.assignee_organization",
    "cpc_current.cpc_group_id",
]


def _date_int(patent_date: str | None) -> int:
    """'2024-06-18' -> 20240618; missing -> 0."""
    if not patent_date:
        return 0
    try:
        y, m, d = patent_date.split("-")
        return int(y) * 10000 + int(m) * 100 + int(d)
    except ValueError:
        return 0


def build_lens_a_body(aliases: Sequence[str], window: DateWindow,
                      size: int) -> dict:
    return {
        "q": {"_and": [
            {"_gte": {"patent_date": window.start.isoformat()}},
            {"_lte": {"patent_date": window.end.isoformat()}},
            {"_or": [{"_text_phrase": {"assignees.assignee_organization": a}}
                     for a in aliases]},
        ]},
        "f": _FIELDS,
        "o": {"size": size},
        "s": [{"patent_date": "desc"}],
    }


def build_lens_b_body(prefixes: Sequence[str], window: DateWindow,
                      size: int) -> dict:
    cpc_or = [{"_begins": {"cpc_current.cpc_group_id": p}} for p in prefixes]
    q_and = [
        {"_gte": {"patent_date": window.start.isoformat()}},
        {"_lte": {"patent_date": window.end.isoformat()}},
    ]
    if cpc_or:
        q_and.append({"_or": cpc_or})
    return {
        "q": {"_and": q_and},
        "f": _FIELDS,
        "o": {"size": size},
        "s": [{"patent_date": "desc"}],
    }


def _row_to_patent(row: dict) -> Patent:
    assignees = tuple(
        a.get("assignee_organization")
        for a in (row.get("assignees") or [])
        if a.get("assignee_organization")
    )
    cpc = tuple(
        c.get("cpc_group_id")
        for c in (row.get("cpc_current") or [])
        if c.get("cpc_group_id")
    )
    pid = row.get("patent_id") or ""
    return Patent(
        publication_number=f"US{pid}" if pid else "US",
        title=(row.get("patent_title") or "").strip(),
        abstract=(row.get("patent_abstract") or "").strip(),
        assignees=assignees,
        cpc_codes=cpc,
        publication_date=_date_int(row.get("patent_date")),
        country_code="US",
    )


class PatentsViewSource:
    """PatentSearch API implementation of PatentSource."""

    def __init__(self, api_key: str | None, timeout: int = 30):
        if not api_key:
            raise ValueError(
                "PatentsView needs a free API key. Set PATENTSVIEW_API_KEY "
                "(get one at https://patentsview.org/apis).")
        import requests  # lazy
        self._requests = requests
        self.api_key = api_key
        self.timeout = timeout

    def _post(self, body: dict) -> list[Patent]:
        resp = self._requests.post(
            API_URL, json=body,
            headers={"X-Api-Key": self.api_key,
                     "Content-Type": "application/json"},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return [_row_to_patent(p) for p in (data.get("patents") or [])]

    def lens_a_patents(self, competitors: Sequence[Competitor],
                       window: DateWindow) -> list[Patent]:
        aliases = [a for c in competitors for a in c.aliases]
        # PatentsView caps phrase clauses; chunk to stay well under limits.
        out: list[Patent] = []
        seen: set[str] = set()
        for i in range(0, len(aliases), 25):
            chunk = aliases[i:i + 25]
            for p in self._post(build_lens_a_body(chunk, window, 200)):
                if p.publication_number not in seen:
                    seen.add(p.publication_number)
                    out.append(p)
        return out

    def lens_b_candidates(self, problem: Problem, window: DateWindow,
                          limit: int) -> list[Patent]:
        body = build_lens_b_body(problem.cpc_prefixes, window, limit)
        return [p for p in self._post(body) if p.abstract]
