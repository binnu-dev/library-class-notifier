"""Runtime configuration for the patent-landscape workflow.

All knobs are read from the environment so the same code runs locally and in
CI. Nothing here requires credentials to import — the BigQuery / email / SMTP
checks happen lazily when those subsystems are actually used.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, timedelta


def _yyyymmdd(d: date) -> int:
    """BigQuery's patents dataset stores dates as INT64 like 20240115."""
    return d.year * 10000 + d.month * 100 + d.day


@dataclass(frozen=True)
class DateWindow:
    """The publication window scanned this run, inclusive on both ends."""

    start: date
    end: date

    @property
    def start_int(self) -> int:
        return _yyyymmdd(self.start)

    @property
    def end_int(self) -> int:
        return _yyyymmdd(self.end)

    @property
    def label(self) -> str:
        """Human label for the brief header, e.g. ``2026.06.24주``."""
        return f"{self.end.year}.{self.end.month:02d}.{self.end.day:02d}주"

    def __str__(self) -> str:
        return f"{self.start.isoformat()} → {self.end.isoformat()}"


def default_window(today: date | None = None, lookback_days: int = 7) -> DateWindow:
    """The trailing ``lookback_days`` window ending yesterday.

    The trigger runs Tue/Wed after the weekly gazette drops; we scan the last
    seven days of newly published documents. ``end`` is yesterday so we never
    ask for a not-yet-complete day.
    """
    today = today or date.today()
    end = today - timedelta(days=1)
    start = end - timedelta(days=lookback_days - 1)
    return DateWindow(start=start, end=end)


@dataclass
class Settings:
    """Everything the pipeline needs, assembled from the environment."""

    # Data source: "demo" | "patentsview" | "bigquery"
    source: str = "bigquery"
    gcp_project: str | None = None
    bigquery_location: str = "US"
    patentsview_api_key: str | None = None

    # Embeddings
    embedding_backend: str = "auto"      # auto | sentence-transformers | hashing
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Lens sizing
    lens_b_candidate_limit: int = 400    # CPC-prefiltered rows pulled per problem
    lens_b_top_k: int = 3                # items kept per problem after ranking
    lens_b_min_similarity: float = 0.30  # drop weak semantic matches
    lens_a_limit_per_competitor: int = 10

    # Window
    lookback_days: int = 7

    # Email delivery (SMTP)
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    email_from: str | None = None
    email_to: tuple[str, ...] = field(default_factory=tuple)

    # Behaviour
    dry_run: bool = False                # build brief but do not send email
    out_path: str | None = None          # also write the brief text to this file

    @classmethod
    def from_env(cls, env: dict | None = None) -> "Settings":
        env = env if env is not None else os.environ

        def _get(name: str, default: str | None = None) -> str | None:
            val = env.get(name)
            return val if val not in (None, "") else default

        def _int(name: str, default: int) -> int:
            raw = _get(name)
            return int(raw) if raw is not None else default

        def _float(name: str, default: float) -> float:
            raw = _get(name)
            return float(raw) if raw is not None else default

        recipients = _get("PATENT_EMAIL_TO", "") or ""
        to = tuple(r.strip() for r in recipients.replace(";", ",").split(",")
                   if r.strip())

        return cls(
            source=_get("PATENT_SOURCE", "bigquery"),
            gcp_project=_get("GCP_PROJECT") or _get("GOOGLE_CLOUD_PROJECT"),
            bigquery_location=_get("BIGQUERY_LOCATION", "US"),
            patentsview_api_key=_get("PATENTSVIEW_API_KEY"),
            embedding_backend=_get("EMBEDDING_BACKEND", "auto"),
            embedding_model=_get("EMBEDDING_MODEL",
                                 "sentence-transformers/all-MiniLM-L6-v2"),
            lens_b_candidate_limit=_int("LENS_B_CANDIDATE_LIMIT", 400),
            lens_b_top_k=_int("LENS_B_TOP_K", 3),
            lens_b_min_similarity=_float("LENS_B_MIN_SIMILARITY", 0.30),
            lens_a_limit_per_competitor=_int("LENS_A_LIMIT", 10),
            lookback_days=_int("PATENT_LOOKBACK_DAYS", 7),
            smtp_host=_get("SMTP_HOST"),
            smtp_port=_int("SMTP_PORT", 587),
            smtp_user=_get("SMTP_USER"),
            smtp_password=_get("SMTP_PASSWORD"),
            email_from=_get("EMAIL_FROM") or _get("SMTP_USER"),
            email_to=to,
            dry_run=_get("PATENT_DRY_RUN", "false").lower() in ("1", "true", "yes"),
            out_path=_get("PATENT_OUT"),
        )
