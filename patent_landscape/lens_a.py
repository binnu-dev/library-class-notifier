"""Lens A — competitor tracking (deterministic assignee query)."""

from __future__ import annotations

from typing import Sequence

from .config import DateWindow, Settings
from .models import BriefItem, Patent
from .registry import Competitor, active_competitors
from .scoring import one_liner, score_lens_a
from .source import PatentSource


def _attribute(patent: Patent,
               competitors: Sequence[Competitor]) -> tuple[Competitor, str] | None:
    """Find which competitor (and matched assignee string) owns this doc."""
    joined = [a.lower() for a in patent.assignees]
    for comp in competitors:
        for alias in comp.aliases:
            al = alias.lower()
            for name_l, name in zip(joined, patent.assignees):
                if al in name_l:
                    return comp, name
    return None


def run_lens_a(source: PatentSource, settings: Settings,
               window: DateWindow) -> list[BriefItem]:
    competitors = active_competitors()
    patents = source.lens_a_patents(competitors, window)

    # Attribute, score, and de-duplicate by publication number.
    scored: list[tuple[Competitor, str, Patent, int]] = []
    seen: set[str] = set()
    for p in patents:
        if p.publication_number in seen:
            continue
        seen.add(p.publication_number)
        attribution = _attribute(p, competitors)
        if attribution is None:
            continue
        comp, matched_name = attribution
        scored.append((comp, matched_name, p, score_lens_a(p, window)))

    # Cap per competitor (keep that competitor's strongest signals).
    cap = settings.lens_a_limit_per_competitor
    per_comp: dict[str, int] = {}
    kept: list[tuple[Competitor, str, Patent, int]] = []
    for row in sorted(scored, key=lambda r: r[3], reverse=True):
        comp = row[0]
        if per_comp.get(comp.key, 0) >= cap:
            continue
        per_comp[comp.key] = per_comp.get(comp.key, 0) + 1
        kept.append(row)

    kept.sort(key=lambda r: r[3], reverse=True)

    items: list[BriefItem] = []
    for i, (comp, matched_name, patent, score) in enumerate(kept, start=1):
        items.append(BriefItem(
            item_id=f"A-{i:02d}",
            patent=patent,
            one_liner=one_liner(patent),
            signal=f"{comp.display} — {matched_name} 신규 공개",
            score=score,
        ))
    return items
