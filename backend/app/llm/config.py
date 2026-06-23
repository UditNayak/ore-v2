"""Typed schema + loader for the LLM gateway configuration (config/llm.yaml).

The YAML shape is:

    tiers:
      smart:
        - {provider: groq, model: llama-3.3-70b-versatile, temperature: 0.2}
      cheap:
        - {provider: groq, model: llama-3.1-8b-instant}

Each tier is an *ordered* list of candidates: index 0 is primary, the rest are
fallbacks tried in order. See docs/decisions/0002-llm-gateway-multiprovider.md.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class CandidateConfig(BaseModel):
    """A single provider/model option within a tier."""

    provider: str
    model: str
    temperature: float = 0.2
    max_tokens: int | None = None
    # Any extra provider-specific kwargs passed through to LiteLLM untouched.
    extra: dict[str, Any] = Field(default_factory=dict)

    @property
    def litellm_model(self) -> str:
        """The `provider/model` string LiteLLM expects (e.g. ``groq/llama-3.1-8b-instant``)."""
        return f"{self.provider}/{self.model}"

    @property
    def label(self) -> str:
        """Human-readable identifier for logs/metrics."""
        return self.litellm_model


class LLMConfig(BaseModel):
    """Top-level gateway configuration: a map of tier name -> ordered candidates."""

    tiers: dict[str, list[CandidateConfig]]

    @field_validator("tiers")
    @classmethod
    def _tiers_non_empty(
        cls, tiers: dict[str, list[CandidateConfig]]
    ) -> dict[str, list[CandidateConfig]]:
        if not tiers:
            raise ValueError("config must define at least one tier")
        for name, candidates in tiers.items():
            if not candidates:
                raise ValueError(f"tier '{name}' must list at least one candidate")
        return tiers


def load_llm_config(path: str | Path) -> LLMConfig:
    """Load and validate the gateway configuration from a YAML file."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a mapping at the top level")
    return LLMConfig.model_validate(raw)
