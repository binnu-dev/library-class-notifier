"""Operational registry derived from the human-edited anchors.

The markdown anchors (``anchors/competitors.md`` and ``anchors/problems.md``)
are what a human reads and edits. This module is the *query-level* layer that
those anchors map onto:

* ``COMPETITORS`` — each competitor's English assignee-name aliases, used to
  match ``assignee_harmonized.name`` in BigQuery. This is where the spec's
  "법인명 표기 흔들림(Robert Bosch GmbH vs Bosch)은 구현 단계에서 정규화" lives.
* ``PROBLEMS`` — each problem's embedding sentence (lens B query text) and the
  CPC subclass prefilters that narrow the search universe to the neighbouring
  industries named in the anchor.

Keep this file in sync with the anchors when the anchors change.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# --------------------------------------------------------------------------- #
# Lens A — competitors
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Competitor:
    """A tracked competitor and the assignee-name fragments that identify it.

    ``aliases`` are matched case-insensitively as substrings against
    ``assignee_harmonized.name`` so that the many legal-entity spellings of a
    single company (e.g. ``Robert Bosch GmbH``, ``Bosch Sensortec``) all map
    back to one competitor.
    """

    key: str
    display: str          # Korean label as it appears in the anchor
    group: str            # "OEM" | "Supplier"
    aliases: tuple[str, ...]
    backlog: bool = False


COMPETITORS: tuple[Competitor, ...] = (
    # --- OEM ---------------------------------------------------------------
    Competitor("hyundai_kia", "현대·기아", "OEM",
               ("Hyundai Motor", "Kia Corp", "Kia Motors")),
    Competitor("toyota_honda", "토요타·혼다", "OEM",
               ("Toyota", "Honda Motor", "Honda Giken")),
    Competitor("vw_mb_bmw", "VW·Mercedes·BMW", "OEM",
               ("Volkswagen", "Audi", "Porsche",
                "Mercedes-Benz", "Daimler",
                "Bayerische Motoren Werke", "BMW")),
    Competitor("ford_stellantis", "Ford·Stellantis", "OEM",
               ("Ford Global Technologies", "Ford Motor",
                "Stellantis", "FCA US", "Fiat Chrysler", "Peugeot", "PSA")),
    Competitor("tesla", "테슬라", "OEM",
               ("Tesla",)),
    Competitor("byd_geely", "BYD·지리", "OEM",
               ("BYD", "Geely", "Zhejiang Geely")),
    # --- Supplier ----------------------------------------------------------
    Competitor("bosch_conti_zf", "Bosch·Continental·ZF", "Supplier",
               ("Robert Bosch", "Bosch", "Continental Auto", "Continental Teves",
                "ZF Friedrichshafen", "ZF Active Safety")),
    Competitor("denso_aisin", "Denso·Aisin", "Supplier",
               ("Denso", "Aisin")),
    Competitor("mobileye_nvidia", "Mobileye·Nvidia", "Supplier",
               ("Mobileye", "Nvidia")),
    Competitor("battery_trio", "LG엔솔·삼성SDI·CATL", "Supplier",
               ("LG Energy Solution", "LG Chem", "Samsung SDI",
                "Contemporary Amperex", "CATL")),
    Competitor("hyundai_mobis", "현대모비스", "Supplier",
               ("Hyundai Mobis",)),
    # --- Backlog (not queried in v1) --------------------------------------
    Competitor("apple", "Apple", "Backlog", ("Apple Inc",), backlog=True),
    Competitor("huawei", "Huawei", "Backlog", ("Huawei",), backlog=True),
    Competitor("xiaomi", "Xiaomi", "Backlog", ("Xiaomi", "Beijing Xiaomi"),
               backlog=True),
)

# GM is the company itself — explicitly excluded, kept here for documentation.
EXCLUDED_ASSIGNEES: tuple[str, ...] = ("General Motors", "GM Global Technology")


def active_competitors() -> list[Competitor]:
    """Competitors actually queried in v1 (backlog entries dropped)."""
    return [c for c in COMPETITORS if not c.backlog]


# CPC subclasses that keep lens A focused on automotive-relevant art. A
# competitor like Samsung or Nvidia files across many fields; this filter keeps
# the brief about mobility tech rather than, say, phone displays. Tunable.
LENS_A_CPC_PREFIX: tuple[str, ...] = (
    "B60",  # vehicles in general
    "B62D",  # motor vehicles, trailers
    "G05D",  # systems for controlling non-electric variables (autonomy)
    "G08G",  # traffic control
    "H01M",  # batteries / fuel cells
    "H02J",  # power supply / charging
    "G01S",  # radar/lidar/sonar
    "G06V",  # image/video recognition (perception)
)


# --------------------------------------------------------------------------- #
# Lens B — problem catalogue
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Problem:
    """A problem from the catalogue plus its lens-B matching parameters.

    ``sentence`` is embedded once and compared against patent-abstract
    embeddings. ``cpc_prefixes`` narrows the candidate universe to the
    neighbouring industries before the (expensive) semantic ranking.
    """

    key: str            # "P1" .. "P8"
    title: str          # short label as in the anchor
    neighbours: str     # neighbouring industries (anchor text, for the brief)
    sentence: str       # embedding query text
    cpc_prefixes: tuple[str, ...]
    backlog: bool = False


PROBLEMS: tuple[Problem, ...] = (
    Problem(
        "P1", "고밀도 셀 스택 방열", "데이터센터 냉각 / LED / 전력반도체",
        "Removing heat from a densely packed stack of cells or electronic "
        "components: thermal management, cooling plates, heat spreading and "
        "dissipation in high power-density assemblies.",
        ("F28",        # heat exchange in general
         "H05K7",      # cooling of electronic apparatus
         "H01L23",     # semiconductor cooling/packaging
         "F21V29",     # cooling of lighting devices
         "H01M10/65"), # battery temperature control
    ),
    Problem(
        "P2", "NVH 저감", "항공 캐빈 / HVAC / 가전",
        "Reducing noise, vibration and harshness: structural damping, "
        "acoustic insulation and active vibration control in cabins, ducts "
        "and machinery.",
        ("F16F",       # springs, shock absorbers, vibration dampers
         "G10K11/16",  # sound absorbing / insulating
         "B64C1",      # aircraft fuselage / cabin
         "F24F13/24"), # silencers for air-conditioning
    ),
    Problem(
        "P3", "경량화 (강성 손실 없이)", "항공우주 / 스포츠장비 / 건축",
        "Reducing mass without losing stiffness: lightweight composite and "
        "lattice structures, topology optimisation, high specific-strength "
        "materials.",
        ("B32B",       # layered / composite products
         "B64C",       # aerospace structures
         "C08J5",      # fibre-reinforced composites
         "B29C70"),    # shaping composites
    ),
    Problem(
        "P4", "악조건 퍼셉션 (비·안개·역광)", "의료영상 / 국방 / 농업드론",
        "Robust perception in adverse conditions such as rain, fog and "
        "backlight: image dehazing, sensor fusion and denoising for reliable "
        "detection in low-visibility scenes.",
        ("G06V10",     # image recognition arrangements
         "G06T5",      # image enhancement / restoration
         "G01S7/48",   # lidar signal processing
         "H04N23"),    # cameras / image pickup
    ),
    Problem(
        "P5", "체결부 내구·피로", "풍력터빈 / 철도 / 교량",
        "Durability and fatigue life of fasteners and joints: bolted and "
        "riveted connections, fatigue-resistant joining and loosening "
        "prevention under cyclic load.",
        ("F16B",       # fasteners, bolts, joints
         "F03D",       # wind motors
         "E01D",       # bridges
         "B61"),       # railways
    ),
    Problem(
        "P6", "커넥터·하우징 밀폐/방수", "해양장비 / 의료기기 / 가전",
        "Sealing and waterproofing of connectors and housings: ingress "
        "protection, gaskets and watertight enclosures for electrical "
        "connections.",
        ("H01R13/52",  # sealed/waterproof connectors
         "H05K5",      # casings / housings for apparatus
         "B63",        # ships / marine
         "F16J15"),    # sealings / gaskets
    ),
    Problem(
        "P7", "협소공간 하네스·부품 라우팅", "로보틱스 / 웨어러블 / 내시경",
        "Routing wiring harnesses and components through tight spaces: "
        "flexible cable management, compact routing and strain relief in "
        "confined volumes.",
        ("H02G3",      # installation of cables / wiring
         "B25J",       # manipulators / robots
         "A61B1",      # endoscopes
         "H01B7"),     # flexible cables
    ),
    Problem(
        "P8", "실내공간 활용·모듈러 패키징", "항공 갤리·시트 / RV·캠핑카 / 요트 / 건축 모듈러",
        "Making the most of interior space with modular packaging: "
        "reconfigurable, stowable and convertible interior modules and "
        "fittings for compact living and working spaces.",
        ("B64D11",     # aircraft cabin / galley / seats
         "B60N2",      # vehicle seats / interior
         "E04B1/348",  # modular building units
         "B60P3"),     # vehicles adapted for special loads (RV-ish)
    ),
    # --- Backlog (not searched in v1) -------------------------------------
    Problem(
        "PX", "인라인 결함 검출", "백로그",
        "In-line defect detection on a production line.",
        (),
        backlog=True,
    ),
)


def active_problems() -> list[Problem]:
    """Problems actually searched in v1 (backlog entries dropped)."""
    return [p for p in PROBLEMS if not p.backlog]
