"""Orchestration: source → two lenses → brief → delivery.

``build_brief`` is source-agnostic (takes an injected ``PatentSource`` and
``EmbeddingProvider``) so it can be unit-tested with fakes. ``run`` wires up
the real BigQuery source / embedding backend and handles delivery.
"""

from __future__ import annotations

from .brief import Brief, render_text
from .config import DateWindow, Settings, default_window
from .embeddings import EmbeddingProvider, get_provider
from .lens_a import run_lens_a
from .lens_b import run_lens_b
from .source import PatentSource


def build_brief(source: PatentSource, settings: Settings,
                embedder: EmbeddingProvider, window: DateWindow) -> Brief:
    lens_a = run_lens_a(source, settings, window)
    lens_b = run_lens_b(source, settings, embedder, window)
    return Brief(window=window, lens_a=lens_a, lens_b=lens_b)


def run(settings: Settings | None = None,
        window: DateWindow | None = None) -> Brief:
    """Full run against BigQuery; sends email unless dry_run is set."""
    settings = settings or Settings.from_env()
    window = window or default_window(lookback_days=settings.lookback_days)

    from .bigquery_source import BigQuerySource  # lazy: needs the GCP client
    source = BigQuerySource(project=settings.gcp_project,
                            location=settings.bigquery_location)
    embedder = get_provider(settings.embedding_backend, settings.embedding_model)

    print(f"[patent-landscape] window {window} "
          f"| embeddings={embedder.name}")
    brief = build_brief(source, settings, embedder, window)
    print(f"[patent-landscape] built brief: {brief.total_items} items "
          f"(A {len(brief.lens_a)} · B {len(brief.lens_b)})")

    if settings.dry_run:
        print("[patent-landscape] DRY RUN — not sending email.\n")
        print(render_text(brief))
        return brief

    from .email_delivery import send_brief
    send_brief(brief, settings)
    print(f"[patent-landscape] sent to {', '.join(settings.email_to)}")
    return brief
