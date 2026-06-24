"""Entry point for the weekly patent-landscape run.

Usage:
    python -m patent_landscape.main            # full run (queries + email)
    python -m patent_landscape.main --dry-run  # build & print brief, no email

Env: see patent_landscape/README.md. The trigger (GitHub Actions weekly cron)
calls this module.
"""

from __future__ import annotations

import argparse
import sys

from datetime import date

from .config import DateWindow, Settings, default_window
from .pipeline import run
from .sample_data import SAMPLE_WINDOW


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Weekly patent landscape brief")
    parser.add_argument("--source", choices=["demo", "patentsview", "bigquery"],
                        default=None,
                        help="Data source (overrides PATENT_SOURCE). "
                             "'demo' runs offline on bundled sample data.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Build and print the brief without sending email.")
    parser.add_argument("--out", default=None,
                        help="Also write the brief text to this file.")
    parser.add_argument("--lookback-days", type=int, default=None,
                        help="Override the publication window length.")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    if args.source:
        settings.source = args.source
    if args.dry_run:
        settings.dry_run = True
    if args.out:
        settings.out_path = args.out
    if args.lookback_days:
        settings.lookback_days = args.lookback_days

    # The demo source carries its own fixed, dated sample window so it runs the
    # same regardless of the machine clock.
    if settings.source == "demo" and args.lookback_days is None:
        window = SAMPLE_WINDOW
    else:
        window = default_window(lookback_days=settings.lookback_days)

    try:
        run(settings=settings, window=window)
    except Exception as exc:  # noqa: BLE001 - surface a clean CI failure
        print(f"[patent-landscape] FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
