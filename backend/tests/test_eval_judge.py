"""LLM-as-judge for root cause — short-circuit + embedding fallback (no live LLM)."""

from app.eval import judge as judge_mod
from app.eval.judge import judge_root_cause


async def test_judge_returns_zero_when_either_side_missing() -> None:
    assert await judge_root_cause("", "the pool was exhausted") == 0.0
    assert await judge_root_cause("something", None) == 0.0


async def test_judge_falls_back_to_embedding_on_failure(monkeypatch) -> None:
    async def _boom(*args: object, **kwargs: object) -> object:
        raise ValueError("judge parse failed")

    monkeypatch.setattr(judge_mod, "structured_call", _boom)
    score = await judge_root_cause(
        "the backfill exhausted the shared db connection pool",
        "the shared database connection pool was exhausted by the backfill",
    )
    assert 0.0 <= score <= 1.0
    assert score > 0.3  # related texts → non-trivial embedding similarity
