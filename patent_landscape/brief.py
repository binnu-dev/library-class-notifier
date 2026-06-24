"""Render the weekly brief (the single email body a human reads).

Layout follows the spec exactly: an [A] competitor section as a flat list and
a [B] cross-industry section grouped by problem (P-order). Each line carries a
stable ID (A-01, B-02, …) reused in v2 for reply parsing.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import DateWindow
from .models import BriefItem
from .registry import active_problems


@dataclass
class Brief:
    window: DateWindow
    lens_a: list[BriefItem]
    lens_b: list[BriefItem]

    @property
    def subject(self) -> str:
        return f"주간 특허 랜드스케이프 — {self.window.label}"

    @property
    def total_items(self) -> int:
        return len(self.lens_a) + len(self.lens_b)


def _line(item: BriefItem, indent: str) -> str:
    lens = "신호" if item.item_id.startswith("A") else "차용"
    return (f"{indent}{item.item_id} | {item.patent.title or '(무제)'} | "
            f"{item.one_liner} | {lens}: {item.signal} | "
            f"점수 {item.score:02d} | {item.patent.url}")


def render_text(brief: Brief) -> str:
    """Plain-text brief body."""
    out: list[str] = []
    out.append(f"주간 특허 랜드스케이프 — {brief.window.label}")
    out.append(f"(공개 구간 {brief.window})")
    out.append("")

    # --- [A] 경쟁사 동향 ---------------------------------------------------
    out.append("[A] 경쟁사 동향")
    if brief.lens_a:
        for item in brief.lens_a:
            out.append(_line(item, "  "))
    else:
        out.append("  (이번 주 신규 신호 없음)")
    out.append("")

    # --- [B] 이종산업 차용 (problem order) --------------------------------
    out.append("[B] 이종산업 차용")
    by_problem: dict[str, list[BriefItem]] = {}
    for item in brief.lens_b:
        by_problem.setdefault(item.problem_key or "", []).append(item)

    if brief.lens_b:
        for problem in active_problems():
            group = by_problem.get(problem.key)
            if not group:
                continue
            out.append(f"  {problem.key} {problem.title}")
            for item in group:
                out.append(_line(item, "    "))
    else:
        out.append("  (이번 주 차용 후보 없음)")
    out.append("")

    out.append("─" * 60)
    out.append(f"총 {brief.total_items}건 "
               f"(A {len(brief.lens_a)} · B {len(brief.lens_b)}). "
               "'판다'는 항목 ID와 함께 Sean에 수동으로 딥다이브 요청.")
    return "\n".join(out)
