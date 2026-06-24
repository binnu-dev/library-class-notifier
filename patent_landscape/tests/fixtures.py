"""Shared fake patents for the test suite."""

from __future__ import annotations

from patent_landscape.models import Patent

# A small, hand-built pool spanning both lenses. publication_date is yyyymmdd
# inside a 2026-06-15..2026-06-21 window used by the tests.

POOL = [
    # --- Lens A: competitor docs ------------------------------------------
    Patent(
        publication_number="US-2026111111-A1",
        title="Battery pack thermal management for electric vehicle",
        abstract="A cooling plate distributes coolant across a high-density "
                 "battery cell stack to remove heat. The vehicle battery pack "
                 "maintains uniform temperature under fast charging.",
        assignees=("Robert Bosch GmbH",),
        cpc_codes=("H01M10/65", "B60L58/26"),
        publication_date=20260618,
        country_code="US",
    ),
    Patent(
        publication_number="US-2026222222-A1",
        title="Autonomous driving perception under fog",
        abstract="A sensor fusion system enhances camera images degraded by "
                 "fog and backlight for reliable object detection by an "
                 "automated driving controller.",
        assignees=("Mobileye Vision Technologies Ltd",),
        cpc_codes=("G06V10/82", "G01S7/48", "B60W30/00"),
        publication_date=20260620,
        country_code="US",
    ),
    Patent(
        publication_number="KR-2026333333-A",
        title="Vehicle seat with modular stowage",
        abstract="A reconfigurable vehicle seat folds into a modular interior "
                 "package to maximise cabin space.",
        assignees=("Hyundai Motor Company", "Kia Corporation"),
        cpc_codes=("B60N2/30",),
        publication_date=20260616,
        country_code="KR",
    ),
    # --- Lens B only: cross-industry docs (no competitor assignee) ---------
    Patent(
        publication_number="US-2026444444-A1",
        title="Liquid cooling for data center server racks",
        abstract="A cold plate assembly removes heat from densely packed "
                 "server processors in a data center, dissipating thermal load "
                 "from a high power-density stack of electronic components.",
        assignees=("Acme Datacenter Cooling Inc",),
        cpc_codes=("H05K7/20", "F28D15/02"),
        publication_date=20260617,
        country_code="US",
    ),
    Patent(
        publication_number="EP-2026555555-A1",
        title="Modular aircraft galley insert",
        abstract="A stowable, reconfigurable galley module makes the most of "
                 "interior cabin space in an aircraft, with convertible "
                 "fittings for compact working areas.",
        assignees=("Aero Interiors SA",),
        cpc_codes=("B64D11/04",),
        publication_date=20260619,
        country_code="EP",
    ),
    # --- Noise: in window but irrelevant to both lenses -------------------
    Patent(
        publication_number="US-2026666666-A1",
        title="Method of brewing coffee",
        abstract="A coffee machine controls water temperature for brewing.",
        assignees=("Generic Appliances Co",),
        cpc_codes=("A47J31/00",),
        publication_date=20260618,
        country_code="US",
    ),
    # --- Out of window: should never appear ------------------------------
    Patent(
        publication_number="US-2026777777-A1",
        title="Old battery cooling patent",
        abstract="Battery cooling stack heat dissipation cold plate.",
        assignees=("Robert Bosch GmbH",),
        cpc_codes=("H01M10/65",),
        publication_date=20260101,
        country_code="US",
    ),
]
