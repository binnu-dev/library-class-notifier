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

from .config import Settings, default_window
from .pipeline import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Weekly patent landscape brief")
    parser.add_argument("--dry-run", action="store_true",
                        help="Build and print the brief without sending email.")
    parser.add_argument("--lookback-days", type=int, default=None,
                        help="Override the publication window length.")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    if args.dry_run:
        settings.dry_run = True
    if args.lookback_days:
        settings.lookback_days = args.lookback_days

    window = default_window(lookback_days=settings.lookback_days)

    try:
        run(settings=settings, window=window)
    except Exception as exc:  # noqa: BLE001 - surface a clean CI failure
        print(f"[patent-landscape] FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
