"""LLM cost/quality tiers.

A *tier* is a level of capability, not a model. Nodes pick a tier by intent:
cheap work (classification, planning, sufficiency checks) vs. high-quality work
(reasoning, critique). The concrete model behind each tier lives in config/llm.yaml.
"""

from enum import StrEnum


class Tier(StrEnum):
    """Capability tiers a caller can request from the gateway."""

    CHEAP = "cheap"
    SMART = "smart"
