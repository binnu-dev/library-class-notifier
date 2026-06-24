"""Tests for the lightweight (free) path: demo source + PatentsView builders."""

from __future__ import annotations

from patent_landscape.brief import render_text
from patent_landscape.config import Settings
from patent_landscape.embeddings import HashingProvider
from patent_landscape.patentsview_source import (
    build_lens_a_body, build_lens_b_body, _date_int, _row_to_patent,
)
from patent_landscape.pipeline import build_brief, build_source, deliver
from patent_landscape.registry import active_competitors, active_problems
from patent_landscape.sample_data import SAMPLE_PATENTS, SAMPLE_WINDOW


def _demo_settings(**kw):
    base = dict(source="demo", embedding_backend="hashing",
                lens_b_min_similarity=0.30)
    base.update(kw)
    return Settings(**base)


# --------------------------------------------------------------------------- #
# demo source / sample data
# --------------------------------------------------------------------------- #

def test_demo_source_is_fake_over_sample():
    src = build_source(_demo_settings())
    a = src.lens_a_patents(active_competitors(), SAMPLE_WINDOW)
    assert any("Bosch" in " ".join(p.assignees) for p in a)
    # coffee noise patent is never a competitor hit
    assert all("Generic Appliances" not in " ".join(p.assignees) for p in a)


def test_demo_full_brief_covers_all_problems():
    settings = _demo_settings()
    brief = build_brief(build_source(settings), settings,
                        HashingProvider(), SAMPLE_WINDOW)
    text = render_text(brief)
    assert len(brief.lens_a) >= 5
    # every active problem should surface at least one borrow candidate
    seen = {i.problem_key for i in brief.lens_b}
    for p in active_problems():
        assert p.key in seen, f"{p.key} missing from demo lens B"
    assert "총" in text


def test_sample_window_covers_all_sample_dates():
    for p in SAMPLE_PATENTS:
        assert SAMPLE_WINDOW.start_int <= p.publication_date <= SAMPLE_WINDOW.end_int


def test_deliver_dry_run_prints(capsys):
    settings = _demo_settings(dry_run=True)
    brief = build_brief(build_source(settings), settings,
                        HashingProvider(), SAMPLE_WINDOW)
    deliver(brief, settings)
    out = capsys.readouterr().out
    assert "주간 특허 랜드스케이프" in out
    assert "not emailing" in out


def test_deliver_writes_out_file(tmp_path):
    path = tmp_path / "brief.txt"
    settings = _demo_settings(dry_run=True, out_path=str(path))
    brief = build_brief(build_source(settings), settings,
                        HashingProvider(), SAMPLE_WINDOW)
    deliver(brief, settings)
    assert path.exists()
    assert "[A] 경쟁사 동향" in path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# PatentsView request builders (pure, no network)
# --------------------------------------------------------------------------- #

def test_date_int_parsing():
    assert _date_int("2024-06-18") == 20240618
    assert _date_int(None) == 0
    assert _date_int("garbage") == 0


def test_lens_a_body_has_assignee_and_date():
    body = build_lens_a_body(["Toyota", "Honda Motor"], SAMPLE_WINDOW, 50)
    clauses = body["q"]["_and"]
    assert {"_gte": {"patent_date": "2026-06-15"}} in clauses
    assert {"_lte": {"patent_date": "2026-06-24"}} in clauses
    org_or = [c for c in clauses if "_or" in c][0]["_or"]
    assert {"_text_phrase": {"assignees.assignee_organization": "Toyota"}} in org_or
    assert body["o"] == {"size": 50}


def test_lens_b_body_has_cpc_begins():
    body = build_lens_b_body(("F28", "H05K7"), SAMPLE_WINDOW, 100)
    cpc_or = [c for c in body["q"]["_and"] if "_or" in c][0]["_or"]
    assert {"_begins": {"cpc_current.cpc_group_id": "F28"}} in cpc_or
    assert {"_begins": {"cpc_current.cpc_group_id": "H05K7"}} in cpc_or


def test_row_to_patent_maps_nested_fields():
    row = {
        "patent_id": "11999999",
        "patent_title": "Test",
        "patent_abstract": "An abstract.",
        "patent_date": "2026-06-18",
        "assignees": [{"assignee_organization": "Robert Bosch GmbH"}],
        "cpc_current": [{"cpc_group_id": "H01M10/65"}],
    }
    p = _row_to_patent(row)
    assert p.publication_number == "US11999999"
    assert p.assignees == ("Robert Bosch GmbH",)
    assert p.cpc_codes == ("H01M10/65",)
    assert p.publication_date == 20260618


def test_patentsview_requires_api_key():
    import pytest
    from patent_landscape.patentsview_source import PatentsViewSource
    with pytest.raises(ValueError):
        PatentsViewSource(api_key=None)
