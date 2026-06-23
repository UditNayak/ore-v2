"""Critical-path tests for the LLM gateway.

We deliberately do NOT call real providers here. We inject a fake candidate factory so
we can assert the two things that actually matter and would fail silently:
  1. tier config is parsed correctly, and
  2. a failed primary candidate transparently falls back to the next one.
"""

import pytest
from langchain_core.runnables import Runnable, RunnableLambda

from app.llm.config import CandidateConfig, LLMConfig, load_llm_config
from app.llm.gateway import LLMGateway
from app.llm.tiers import Tier


def _config() -> LLMConfig:
    """A tier whose primary always fails and whose fallback always succeeds."""
    return LLMConfig(
        tiers={
            "smart": [
                CandidateConfig(provider="fail", model="primary"),
                CandidateConfig(provider="ok", model="fallback"),
            ],
            "cheap": [CandidateConfig(provider="ok", model="solo")],
        }
    )


def _fake_factory(candidate: CandidateConfig) -> Runnable:
    """Primary ('fail') raises; everything else echoes its model name."""
    if candidate.provider == "fail":

        def _boom(_: object) -> str:
            raise RuntimeError("primary provider down")

        return RunnableLambda(_boom)
    return RunnableLambda(lambda _: f"ok:{candidate.model}")


# --- config parsing -------------------------------------------------------------------


def test_litellm_model_format() -> None:
    c = CandidateConfig(provider="groq", model="llama-3.1-8b-instant")
    assert c.litellm_model == "groq/llama-3.1-8b-instant"


def test_empty_tiers_rejected() -> None:
    with pytest.raises(ValueError):
        LLMConfig(tiers={})


def test_tier_with_no_candidates_rejected() -> None:
    with pytest.raises(ValueError):
        LLMConfig(tiers={"smart": []})


def test_load_real_config_file() -> None:
    """The shipped config/llm.yaml parses and defines both tiers."""
    cfg = load_llm_config("config/llm.yaml")
    assert {"smart", "cheap"} <= set(cfg.tiers)


# --- gateway behavior -----------------------------------------------------------------


def test_fallback_fires_when_primary_fails() -> None:
    gateway = LLMGateway(_config(), factory=_fake_factory)
    result = gateway.get_llm(Tier.SMART).invoke("hi")
    assert result == "ok:fallback"


def test_single_candidate_tier_runs_directly() -> None:
    gateway = LLMGateway(_config(), factory=_fake_factory)
    assert gateway.get_llm(Tier.CHEAP).invoke("hi") == "ok:solo"


def test_get_llm_is_cached() -> None:
    gateway = LLMGateway(_config(), factory=_fake_factory)
    assert gateway.get_llm("smart") is gateway.get_llm("smart")


def test_unknown_tier_raises() -> None:
    gateway = LLMGateway(_config(), factory=_fake_factory)
    with pytest.raises(KeyError):
        gateway.get_llm("nonexistent")
