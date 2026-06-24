"""Lens B — cross-industry borrowing (CPC prefilter + embedding top-k).

Pipeline per problem:
1. Pull CPC-prefiltered candidates from the source (narrows the universe to
   the neighbouring industries named in the anchor).
2. Embed the problem sentence and every candidate abstract.
3. Rank by cosine similarity, drop weak matches, keep top-k.

The point of step 2-3 (over plain keyword search) is to catch documents that
are *structurally* similar to the problem even when they share no vocabulary.
"""

from __future__ import annotations

from .config import DateWindow, Settings
from .embeddings import EmbeddingProvider, cosine
from .models import BriefItem
from .registry import active_problems
from .scoring import one_liner, score_lens_b
from .source import PatentSource


def run_lens_b(source: PatentSource, settings: Settings,
               embedder: EmbeddingProvider,
               window: DateWindow) -> list[BriefItem]:
    items: list[BriefItem] = []
    counter = 0

    for problem in active_problems():
        candidates = source.lens_b_candidates(
            problem, window, settings.lens_b_candidate_limit)
        candidates = [c for c in candidates if c.abstract]
        if not candidates:
            continue

        # One embedding batch per problem: the sentence + all abstracts.
        vectors = embedder.embed([problem.sentence]
                                 + [c.abstract for c in candidates])
        q_vec, cand_vecs = vectors[0], vectors[1:]

        ranked = sorted(
            ((cosine(q_vec, v), c) for v, c in zip(cand_vecs, candidates)),
            key=lambda t: t[0], reverse=True,
        )

        kept = [(sim, c) for sim, c in ranked
                if sim >= settings.lens_b_min_similarity][: settings.lens_b_top_k]

        for sim, patent in kept:
            counter += 1
            items.append(BriefItem(
                item_id=f"B-{counter:02d}",
                patent=patent,
                one_liner=one_liner(patent),
                signal=(f"{problem.key}에 → {problem.neighbours} 계열, "
                        f"abstract 유사도 {sim:.2f}"),
                score=score_lens_b(sim, patent, problem, window),
                problem_key=problem.key,
                problem_label=problem.title,
            ))

    return items
