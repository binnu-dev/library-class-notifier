"""Orchestration: source → two lenses → brief → delivery.

``build_brief`` is source-agnostic (takes an injected ``PatentSource`` and
``EmbeddingProvider``) so it can be unit-tested with fakes. ``build_source``
picks the concrete source by name. ``run`` wires everything up and delivers.

Delivery rules (kept friction-free for testing):
* ``dry_run`` or no ``SMTP_HOST`` configured → print the brief to stdout.
* email is only attempted when SMTP is configured and ``dry_run`` is off.
* ``out_path`` always also writes the brief text to a file when set.
"""

from __future__ import annotations

from .brief import Brief, render_text
from .config import DateWindow, Settings, default_window
from .embeddings import EmbeddingProvider, get_provider
from .lens_a import run_lens_a
from .lens_b import run_lens_b
from .source import FakePatentSource, PatentSource


def build_source(settings: Settings) -> PatentSource:
    """Resolve the data source from ``settings.source``."""
    name = (settings.source or "bigquery").lower()
    if name == "demo":
        from .sample_data import SAMPLE_PATENTS
        return FakePatentSource(SAMPLE_PATENTS)
    if name == "patentsview":
        from .patentsview_source import PatentsViewSource
        return PatentsViewSource(api_key=settings.patentsview_api_key)
    if name == "bigquery":
        from .bigquery_source import BigQuerySource
        return BigQuerySource(project=settings.gcp_project,
                              location=settings.bigquery_location)
    raise ValueError(f"Unknown source: {settings.source!r} "
                     "(expected demo | patentsview | bigquery)")


def build_brief(source: PatentSource, settings: Settings,
                embedder: EmbeddingProvider, window: DateWindow) -> Brief:
    lens_a = run_lens_a(source, settings, window)
    lens_b = run_lens_b(source, settings, embedder, window)
    return Brief(window=window, lens_a=lens_a, lens_b=lens_b)


def deliver(brief: Brief, settings: Settings) -> None:
    """Write/print/email the brief per the delivery rules above."""
    text = render_text(brief)

    if settings.out_path:
        with open(settings.out_path, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"[patent-landscape] wrote brief to {settings.out_path}")

    email_configured = bool(settings.smtp_host and settings.email_to)
    if settings.dry_run or not email_configured:
        reason = "dry-run" if settings.dry_run else "no SMTP configured"
        print(f"[patent-landscape] not emailing ({reason}); printing brief:\n")
        print(text)
        return

    from .email_delivery import send_brief
    send_brief(brief, settings)
    print(f"[patent-landscape] emailed to {', '.join(settings.email_to)}")


def run(settings: Settings | None = None,
        window: DateWindow | None = None) -> Brief:
    """Full run: build source, run both lenses, deliver the brief."""
    settings = settings or Settings.from_env()
    window = window or default_window(lookback_days=settings.lookback_days)

    source = build_source(settings)
    embedder = get_provider(settings.embedding_backend, settings.embedding_model)

    print(f"[patent-landscape] source={settings.source} | window {window} "
          f"| embeddings={embedder.name}")
    brief = build_brief(source, settings, embedder, window)
    print(f"[patent-landscape] built brief: {brief.total_items} items "
          f"(A {len(brief.lens_a)} · B {len(brief.lens_b)})")

    deliver(brief, settings)
    return brief
