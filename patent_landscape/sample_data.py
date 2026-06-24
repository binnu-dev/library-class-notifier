"""Illustrative sample patents for ``--source demo``.

These are **not live data** — they are hand-written, realistic records (real
companies, plausible abstracts) dated inside the default weekly window so the
whole pipeline runs end-to-end with no API key and no network. The
publication numbers are synthetic, so their Google Patents links won't
resolve; that's expected for the demo. Swap in ``--source patentsview`` (free)
or ``--source bigquery`` for real documents.
"""

from __future__ import annotations

from datetime import date

from .config import DateWindow
from .models import Patent

# Fixed window covering all sample dates below, so --source demo is
# clock-independent.
SAMPLE_WINDOW = DateWindow(start=date(2026, 6, 15), end=date(2026, 6, 24))

# Dates fall inside default_window(today=2026-06-24) = 2026-06-17 .. 2026-06-23.
SAMPLE_PATENTS = [
    # ---- competitor docs (lens A; several also relevant to lens B) -------
    Patent("US-DEMO-0001", "Coolant distribution plate for high-density battery pack",
           "A cooling plate channels coolant across a densely packed stack of "
           "battery cells to remove heat and keep cell temperature uniform "
           "during fast charging of an electric vehicle.",
           ("Robert Bosch GmbH",), ("H01M10/6556", "B60L58/26"), 20260618, "US"),
    Patent("US-DEMO-0002", "Solid-state battery cell with low-vibration housing",
           "A battery module damps structural vibration and reduces noise "
           "transmitted into the vehicle cabin while protecting solid-state "
           "cells from harshness.",
           ("Toyota Motor Corporation",), ("H01M10/0562", "F16F15/00"), 20260619, "US"),
    Patent("US-DEMO-0003", "Reconfigurable vehicle seat with modular stowage",
           "A vehicle seat folds and reconfigures into a modular interior "
           "package, making the most of cabin space for convertible use.",
           ("Hyundai Motor Company", "Kia Corporation"), ("B60N2/3088",), 20260617, "KR"),
    Patent("US-DEMO-0004", "Camera perception robust to fog and backlight",
           "A sensor fusion pipeline restores camera images degraded by fog, "
           "rain and backlight to enable reliable object detection for an "
           "automated driving system.",
           ("Mobileye Vision Technologies Ltd",),
           ("G06V10/82", "G01S7/4802"), 20260620, "US"),
    Patent("US-DEMO-0005", "Liquid-cooled prismatic cell stack",
           "A cold plate dissipates thermal load from a high power-density "
           "stack of prismatic battery cells, spreading heat to a coolant "
           "loop.",
           ("Contemporary Amperex Technology Co",),
           ("H01M10/6567", "F28D1/00"), 20260621, "CN"),
    Patent("US-DEMO-0006", "Fatigue-resistant bolted joint for drivetrain",
           "A bolted connection resists loosening and fatigue under cyclic "
           "load, extending durability of a structural joint in a vehicle "
           "drivetrain.",
           ("ZF Friedrichshafen AG",), ("F16B31/02",), 20260618, "DE"),
    Patent("US-DEMO-0007", "Waterproof high-voltage connector housing",
           "A sealed connector housing provides ingress protection and "
           "watertight sealing for high-voltage electrical connections in "
           "harsh environments.",
           ("Continental Automotive GmbH",), ("H01R13/5202",), 20260619, "DE"),

    # ---- cross-industry docs (lens B only; non-competitor assignees) -----
    Patent("US-DEMO-0101", "Direct liquid cooling for data center server racks",
           "A cold plate assembly removes heat from densely packed server "
           "processors, dissipating thermal load from a high power-density "
           "rack of electronic components in a data center.",
           ("Vertiv Group Corp",), ("H05K7/20272", "F28D15/0266"), 20260617, "US"),
    Patent("US-DEMO-0102", "Stowable modular galley insert for aircraft cabin",
           "A reconfigurable galley module with convertible fittings makes the "
           "most of interior cabin space and stows compactly when not in use.",
           ("Safran Cabin Inc",), ("B64D11/04",), 20260620, "FR"),
    Patent("US-DEMO-0103", "Bolt preload monitoring for wind turbine flange",
           "A fastener assembly monitors preload to prevent loosening and "
           "fatigue failure of a bolted flange joint on a wind turbine tower "
           "under cyclic wind load.",
           ("Vestas Wind Systems A/S",), ("F03D13/20", "F16B31/02"), 20260618, "DK"),
    Patent("US-DEMO-0104", "Flexible cable routing for endoscope tip",
           "A wiring harness routes flexible cables through the confined space "
           "of an endoscope tip with strain relief and compact bend control.",
           ("Olympus Corporation",), ("A61B1/00071", "H01B7/04"), 20260621, "JP"),
    Patent("US-DEMO-0105", "Dehazing for low-visibility medical imaging",
           "An image restoration method removes haze and enhances contrast in "
           "scattering media for reliable detection in degraded medical "
           "imaging scenes.",
           ("Siemens Healthineers AG",), ("G06T5/003",), 20260619, "DE"),
    Patent("US-DEMO-0106", "Watertight subsea instrumentation connector",
           "A gasketed enclosure seals electrical connectors against water "
           "ingress for marine and subsea equipment at depth.",
           ("Teledyne Instruments Inc",), ("H01R13/5219", "F16J15/06"), 20260620, "US"),
    Patent("US-DEMO-0107", "Lightweight composite lattice structural panel",
           "A fibre-reinforced composite panel with an optimised lattice core "
           "reduces mass without losing stiffness for aerospace structures.",
           ("Airbus Operations SAS",), ("B32B3/12", "B64C1/12"), 20260618, "FR"),
    Patent("US-DEMO-0108", "Acoustic damping duct for HVAC system",
           "A duct liner absorbs sound and damps vibration to reduce noise and "
           "harshness transmitted through an HVAC air handling system.",
           ("Daikin Industries Ltd",), ("F24F13/24", "G10K11/162"), 20260621, "JP"),

    # ---- noise: in window, irrelevant to both lenses ---------------------
    Patent("US-DEMO-0900", "Method of brewing coffee",
           "A coffee machine controls water temperature for brewing a beverage.",
           ("Generic Appliances Co",), ("A47J31/00",), 20260618, "US"),
]
