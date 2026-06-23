"""LangChain callback that records per-LLM-call observability: provider/model used,
latency, token usage, and best-effort cost.

This is how we can later tell *which* candidate actually served a request (primary vs.
fallback) and what it cost — feeding the observability requirement.
"""

import time
from typing import Any
from uuid import UUID

import structlog
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

log = structlog.get_logger("llm")


class LLMMetricsCallback(BaseCallbackHandler):
    """Logs latency, model, token usage, and estimated cost for each LLM call."""

    def __init__(self) -> None:
        self._starts: dict[UUID, float] = {}
        self._models: dict[UUID, str] = {}

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._starts[run_id] = time.monotonic()
        params = kwargs.get("invocation_params") or {}
        self._models[run_id] = str(params.get("model") or serialized.get("name") or "unknown")

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        start = self._starts.pop(run_id, None)
        model = self._models.pop(run_id, "unknown")
        latency_s = round(time.monotonic() - start, 3) if start is not None else None

        usage = _extract_token_usage(response)
        cost_usd = _estimate_cost(model, usage)

        log.info(
            "llm_call",
            model=model,
            latency_s=latency_s,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            cost_usd=cost_usd,
        )

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        start = self._starts.pop(run_id, None)
        model = self._models.pop(run_id, "unknown")
        latency_s = round(time.monotonic() - start, 3) if start is not None else None
        # Expected during fallback: the primary candidate fails, the next one is tried.
        log.warning("llm_call_failed", model=model, latency_s=latency_s, error=str(error))


def _extract_token_usage(response: LLMResult) -> dict[str, int]:
    """Pull prompt/completion token counts out of an LLMResult, tolerating shapes."""
    output = response.llm_output or {}
    usage = output.get("token_usage") or output.get("usage") or {}
    return {
        "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
        "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
    }


def _estimate_cost(model: str, usage: dict[str, int]) -> float | None:
    """Best-effort USD cost from token counts using LiteLLM's price map."""
    if not usage.get("prompt_tokens") and not usage.get("completion_tokens"):
        return None
    try:
        import litellm

        prompt_cost, completion_cost = litellm.cost_per_token(
            model=model,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
        )
        return round(prompt_cost + completion_cost, 6)
    except Exception:  # noqa: BLE001 — pricing is best-effort; never break a call over it.
        return None
