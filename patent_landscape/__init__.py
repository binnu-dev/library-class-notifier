"""Weekly external-patent landscape workflow (외부 특허 동향).

Two lenses over the past week's newly published patents:
* Lens A — competitor tracking (deterministic assignee query).
* Lens B — cross-industry borrowing (CPC prefilter + embedding top-k).

Output is a single emailed brief. See README.md for the spec and setup.
"""

__all__ = ["config", "registry", "pipeline"]
