"""End-to-end tests using the in-memory fake source + hashing embeddings."""

from __future__ import annotations

from datetime import date

from patent_landscape.bigquery_source import (
    build_lens_a_query, build_lens_b_query,
)
from patent_landscape.brief import render_text
from patent_landscape.config import DateWindow, Settings, default_window
from patent_landscape.embeddings import HashingProvider, cosine, get_provider
from patent_landscape.lens_a import run_lens_a
from patent_landscape.lens_b import run_lens_b
from patent_landscape.pipeline import build_brief
from patent_landscape.registry import (
    active_competitors, active_problems, PROBLEMS, COMPETITORS,
)
from patent_landscape.source import FakePatentSource
from patent_landscape.tests.fixtures import POOL


WINDOW = DateWindow(start=date(2026, 6, 15), end=date(2026, 6, 21))


def _settings(**kw):
    base = dict(embedding_backend="hashing", lens_b_top_k=3,
                lens_b_min_similarity=0.0, lens_a_limit_per_competitor=10)
    base.update(kw)
    return Settings(**base)


# --------------------------------------------------------------------------- #
# config / window
# --------------------------------------------------------------------------- #

def test_default_window_ends_yesterday():
    w = default_window(today=date(2026, 6, 24), lookback_days=7)
    assert w.end == date(2026, 6, 23)
    assert w.start == date(2026, 6, 17)
    assert w.start_int == 20260617 and w.end_int == 20260623


def test_window_label():
    assert WINDOW.label == "2026.06.21주"


def test_settings_parses_recipients():
    s = Settings.from_env({"PATENT_EMAIL_TO": "a@x.com, b@y.com;c@z.com"})
    assert s.email_to == ("a@x.com", "b@y.com", "c@z.com")


# --------------------------------------------------------------------------- #
# registry
# --------------------------------------------------------------------------- #

def test_backlog_excluded_from_active():
    assert all(not c.backlog for c in active_competitors())
    assert all(not p.backlog for p in active_problems())
    assert any(c.backlog for c in COMPETITORS)   # Apple/Huawei/Xiaomi present
    assert any(p.backlog for p in PROBLEMS)       # 인라인 결함 검출 present


def test_active_problems_are_p1_to_p8():
    keys = [p.key for p in active_problems()]
    assert keys == [f"P{i}" for i in range(1, 9)]


# --------------------------------------------------------------------------- #
# lens A
# --------------------------------------------------------------------------- #

def test_lens_a_finds_competitor_docs_only():
    source = FakePatentSource(POOL)
    items = run_lens_a(source, _settings(), WINDOW)
    pubs = {i.patent.publication_number for i in items}
    # Bosch, Mobileye, Hyundai/Kia docs in-window; coffee/datacenter excluded.
    assert "US-2026111111-A1" in pubs
    assert "US-2026222222-A1" in pubs
    assert "KR-2026333333-A" in pubs
    assert "US-2026444444-A1" not in pubs   # datacenter, no competitor
    assert "US-2026777777-A1" not in pubs   # out of window
    assert all(i.item_id.startswith("A-") for i in items)


def test_lens_a_attribution_signal():
    source = FakePatentSource(POOL)
    items = run_lens_a(source, _settings(), WINDOW)
    bosch = next(i for i in items if i.patent.publication_number == "US-2026111111-A1")
    assert "Robert Bosch GmbH" in bosch.signal
    assert "Bosch" in bosch.signal  # display name


def test_lens_a_per_competitor_cap():
    source = FakePatentSource(POOL)
    items = run_lens_a(source, _settings(lens_a_limit_per_competitor=1), WINDOW)
    # Hyundai/Kia doc counts once; each competitor capped at 1 — still <= total
    assert len(items) <= len(active_competitors())


# --------------------------------------------------------------------------- #
# lens B
# --------------------------------------------------------------------------- #

def test_lens_b_matches_problems_via_cpc_and_similarity():
    source = FakePatentSource(POOL)
    items = run_lens_b(source, _settings(), HashingProvider(), WINDOW)
    by_pub = {i.patent.publication_number: i for i in items}
    # datacenter cooling should land under P1; aircraft galley under P8
    assert "US-2026444444-A1" in by_pub
    assert by_pub["US-2026444444-A1"].problem_key == "P1"
    assert "EP-2026555555-A1" in by_pub
    assert by_pub["EP-2026555555-A1"].problem_key == "P8"
    assert all(i.item_id.startswith("B-") for i in items)


def test_lens_b_similarity_threshold_filters():
    source = FakePatentSource(POOL)
    high = _settings(lens_b_min_similarity=0.99)
    items = run_lens_b(source, high, HashingProvider(), WINDOW)
    assert items == []  # nothing clears an impossible threshold


def test_lens_b_respects_top_k():
    source = FakePatentSource(POOL)
    items = run_lens_b(source, _settings(lens_b_top_k=1), HashingProvider(), WINDOW)
    per_problem: dict[str, int] = {}
    for i in items:
        per_problem[i.problem_key] = per_problem.get(i.problem_key, 0) + 1
    assert all(v <= 1 for v in per_problem.values())


# --------------------------------------------------------------------------- #
# embeddings
# --------------------------------------------------------------------------- #

def test_cosine_bounds():
    assert cosine([1, 0], [1, 0]) == 1.0
    assert abs(cosine([1, 0], [0, 1])) < 1e-9
    assert cosine([0, 0], [1, 1]) == 0.0


def test_hashing_provider_self_similarity_is_high():
    prov = HashingProvider()
    a, b = prov.embed(["battery cooling stack", "battery cooling stack"])
    assert cosine(a, b) > 0.99


def test_get_provider_hashing():
    assert get_provider("hashing").name == "hashing"


# --------------------------------------------------------------------------- #
# brief rendering + IDs
# --------------------------------------------------------------------------- #

def test_brief_renders_both_sections_and_ids():
    source = FakePatentSource(POOL)
    brief = build_brief(source, _settings(), HashingProvider(), WINDOW)
    text = render_text(brief)
    assert "주간 특허 랜드스케이프 — 2026.06.21주" in text
    assert "[A] 경쟁사 동향" in text
    assert "[B] 이종산업 차용" in text
    assert "A-01" in text
    assert "B-01" in text
    # B grouped under problem headers
    assert "P1 고밀도 셀 스택 방열" in text
    assert "https://patents.google.com/patent/" in text


def test_brief_handles_empty_results():
    source = FakePatentSource([])
    brief = build_brief(source, _settings(), HashingProvider(), WINDOW)
    text = render_text(brief)
    assert "이번 주 신규 신호 없음" in text
    assert "이번 주 차용 후보 없음" in text
    assert brief.total_items == 0


# --------------------------------------------------------------------------- #
# SQL builders (pure, no BigQuery)
# --------------------------------------------------------------------------- #

def test_lens_a_query_has_assignee_and_cpc_and_window():
    from patent_landscape.registry import LENS_A_CPC_PREFIX
    sql = build_lens_a_query(active_competitors(), LENS_A_CPC_PREFIX)
    assert "assignee_harmonized" in sql
    assert "publication_date BETWEEN @start AND @end" in sql
    assert "robert bosch" in sql.lower()
    assert "B60" in sql


def test_lens_b_query_has_cpc_prefilter_and_limit():
    p1 = active_problems()[0]
    sql = build_lens_b_query(p1)
    assert "LIMIT @limit" in sql
    assert "cpc" in sql.lower()
    assert "F28" in sql  # P1 prefix


def test_lens_a_query_escapes_quotes():
    from patent_landscape.registry import Competitor
    evil = Competitor("x", "X", "OEM", ("O'Brien",))
    sql = build_lens_a_query([evil], ())
    assert "o\\'brien" in sql.lower()
