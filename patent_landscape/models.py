"""Shared record types passed between the source, lenses and brief."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Patent:
    """One newly published patent document, normalised across sources."""

    publication_number: str
    title: str
    abstract: str
    assignees: tuple[str, ...]
    cpc_codes: tuple[str, ...]
    publication_date: int           # INT64 yyyymmdd
    country_code: str = ""

    @property
    def url(self) -> str:
        """Google Patents permalink for the publication."""
        return f"https://patents.google.com/patent/{self.publication_number}"


@dataclass
class BriefItem:
    """A single ranked line in the brief (lens A or lens B)."""

    item_id: str                    # "A-01", "B-02", ...
    patent: Patent
    one_liner: str                  # ① 무엇인지 1줄
    signal: str                     # ② 왜 이 경쟁사 / 왜 이 Pn 1줄
    score: int                      # ③ 신규성·관련도 점수 (0-100)
    # lens-B grouping metadata (None for lens A)
    problem_key: str | None = None
    problem_label: str | None = None
