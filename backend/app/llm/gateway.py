"""The LLM gateway: turns a *tier* into a ready-to-use LangChain runnable that
transparently falls back across the tier's candidates.

Design (see ADR 0002):
- Each tier is an ordered list of candidates (primary + fallbacks).
- Each candidate is built into a LangChain chat model via an injectable *factory*
  (real factory uses LiteLLM; tests inject a fake one).
- Candidates are composed with `.with_fallbacks()` so a failed primary rolls over
  to the next candidate automatically.
"""

from collections.abc import Callable
from functools import lru_cache
from typing import Any

import structlog
from langchain_core.runnables import Runnable

from app.core.config import get_settings
from app.llm.config import CandidateConfig, LLMConfig, load_llm_config
from app.llm.tiers import Tier

log = structlog.get_logger("llm")

# A factory builds a runnable (chat model) from one candidate's config.
CandidateFactory = Callable[[CandidateConfig], Runnable[Any, Any]]


def _build_litellm_chat(candidate: CandidateConfig) -> Runnable[Any, Any]:
    """Default factory: wrap a candidate as a LiteLLM-backed LangChain chat model.

    Provider API keys are read by LiteLLM from the environment (e.g. GROQ_API_KEY).
    """
    from langchain_litellm import ChatLiteLLM

    return ChatLiteLLM(
        model=candidate.litellm_model,
        temperature=candidate.temperature,
        max_tokens=candidate.max_tokens,
        **candidate.extra,
    )


class LLMGateway:
    """Resolves tiers to fallback-composed runnables, caching the result per tier."""

    def __init__(
        self,
        config: LLMConfig,
        factory: CandidateFactory = _build_litellm_chat,
    ) -> None:
        self._config = config
        self._factory = factory
        self._cache: dict[str, Runnable[Any, Any]] = {}

    def get_llm(self, tier: Tier | str) -> Runnable[Any, Any]:
        """Return a runnable for the tier, with fallbacks across its candidates."""
        name = tier.value if isinstance(tier, Tier) else tier
        if name in self._cache:
            return self._cache[name]

        candidates = self._config.tiers.get(name)
        if not candidates:
            raise KeyError(f"unknown tier '{name}'; configured tiers: {list(self._config.tiers)}")

        primary, *fallbacks = (self._factory(c) for c in candidates)
        runnable = primary.with_fallbacks(fallbacks) if fallbacks else primary

        log.info(
            "tier_resolved",
            tier=name,
            candidates=[c.label for c in candidates],
        )
        self._cache[name] = runnable
        return runnable


def _quiet_litellm() -> None:
    """Silence LiteLLM's stdout chatter and enable rate-limit retries with backoff.

    Retries (with the provider's Retry-After) let the agent survive Groq free-tier TPM
    limits during multi-call runs like the eval harness, at the cost of latency.
    """
    import logging

    import litellm

    litellm.suppress_debug_info = True
    litellm.num_retries = 5
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)


@lru_cache
def get_gateway() -> LLMGateway:
    """Process-wide gateway built from the configured llm.yaml."""
    _quiet_litellm()
    settings = get_settings()
    config = load_llm_config(settings.llm_config_path)
    return LLMGateway(config)
