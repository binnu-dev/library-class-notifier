"""Google Patents public dataset (BigQuery) implementation of PatentSource.

Primary source per the spec: ``patents-public-data.patents.publications``.
Query builders are pure functions so they can be unit-tested without
credentials; ``BigQuerySource`` only adds execution.

USPTO/EPO official APIs are the planned secondary/boost source (see the spec's
"소스" row). They are intentionally left as a documented seam — ``boost_*``
hooks — rather than implemented in v1, because BigQuery's harmonised dataset
already covers both lenses.
"""

from __future__ import annotations

from typing import Sequence

from .config import DateWindow
from .models import Patent
from .registry import Competitor, Problem

TABLE = "`patents-public-data.patents.publications`"


def _escape(value: str) -> str:
    """Escape a string for safe inlining in SQL (registry-sourced, not user)."""
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _cpc_clause(prefixes: Sequence[str], alias: str = "c") -> str:
    if not prefixes:
        return "TRUE"
    ors = " OR ".join(f"{alias}.code LIKE '{_escape(p)}%'" for p in prefixes)
    return f"EXISTS (SELECT 1 FROM UNNEST(cpc) {alias} WHERE {ors})"


def _assignee_clause(aliases: Sequence[str], alias: str = "a") -> str:
    ors = " OR ".join(
        f"LOWER({alias}.name) LIKE '%{_escape(a.lower())}%'" for a in aliases
    )
    return f"EXISTS (SELECT 1 FROM UNNEST(assignee_harmonized) {alias} WHERE {ors})"


_SELECT = f"""
  SELECT
    publication_number,
    (SELECT t.text FROM UNNEST(title_localized) t
       WHERE t.language = 'en' LIMIT 1) AS title,
    (SELECT ab.text FROM UNNEST(abstract_localized) ab
       WHERE ab.language = 'en' LIMIT 1) AS abstract,
    ARRAY(SELECT a.name FROM UNNEST(assignee_harmonized) a) AS assignees,
    ARRAY(SELECT c.code FROM UNNEST(cpc) c) AS cpc_codes,
    publication_date,
    country_code
  FROM {TABLE}
"""


def build_lens_a_query(competitors: Sequence[Competitor],
                       cpc_prefixes: Sequence[str]) -> str:
    """SQL for lens A: competitor assignee × window × automotive CPC."""
    aliases = [a for c in competitors for a in c.aliases]
    where = [
        "publication_date BETWEEN @start AND @end",
        _assignee_clause(aliases),
        _cpc_clause(cpc_prefixes),
        # require an English abstract so the brief one-liner has material
        ("EXISTS (SELECT 1 FROM UNNEST(abstract_localized) ab "
         "WHERE ab.language = 'en' AND ab.text IS NOT NULL)"),
    ]
    return _SELECT + "  WHERE " + "\n    AND ".join(where) + "\n"


def build_lens_b_query(problem: Problem) -> str:
    """SQL for lens B candidate pull: CPC prefilter × window (ranked later)."""
    where = [
        "publication_date BETWEEN @start AND @end",
        _cpc_clause(problem.cpc_prefixes),
        ("EXISTS (SELECT 1 FROM UNNEST(abstract_localized) ab "
         "WHERE ab.language = 'en' AND ab.text IS NOT NULL)"),
    ]
    return (_SELECT + "  WHERE " + "\n    AND ".join(where)
            + "\n  LIMIT @limit\n")


def _row_to_patent(row) -> Patent:
    return Patent(
        publication_number=row["publication_number"],
        title=(row["title"] or "").strip(),
        abstract=(row["abstract"] or "").strip(),
        assignees=tuple(row["assignees"] or ()),
        cpc_codes=tuple(row["cpc_codes"] or ()),
        publication_date=int(row["publication_date"]),
        country_code=row.get("country_code") or "",
    )


class BigQuerySource:
    """Executes the lens queries against BigQuery."""

    def __init__(self, project: str | None = None, location: str = "US"):
        from google.cloud import bigquery  # lazy import

        self._bq = bigquery
        self.client = bigquery.Client(project=project)
        self.location = location

    def _run(self, sql: str, params: list) -> list[Patent]:
        job_config = self._bq.QueryJobConfig(query_parameters=params)
        job = self.client.query(sql, job_config=job_config,
                                location=self.location)
        return [_row_to_patent(dict(r)) for r in job.result()]

    def lens_a_patents(self, competitors: Sequence[Competitor],
                       window: DateWindow) -> list[Patent]:
        from .registry import LENS_A_CPC_PREFIX
        sql = build_lens_a_query(competitors, LENS_A_CPC_PREFIX)
        params = [
            self._bq.ScalarQueryParameter("start", "INT64", window.start_int),
            self._bq.ScalarQueryParameter("end", "INT64", window.end_int),
        ]
        return self._run(sql, params)

    def lens_b_candidates(self, problem: Problem, window: DateWindow,
                          limit: int) -> list[Patent]:
        sql = build_lens_b_query(problem)
        params = [
            self._bq.ScalarQueryParameter("start", "INT64", window.start_int),
            self._bq.ScalarQueryParameter("end", "INT64", window.end_int),
            self._bq.ScalarQueryParameter("limit", "INT64", limit),
        ]
        return self._run(sql, params)
