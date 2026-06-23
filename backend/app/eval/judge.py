"""LLM-as-judge scoring for root-cause identification.

Embedding cosine penalizes correct-but-differently-worded root causes; a judge scores
*meaning* (same underlying cause = high, regardless of phrasing). Runs on the SMART tier
with low effective temperature; falls back to embedding similarity if the call fails.
See docs/EVALUATION.md.
"""

import structlog
from pydantic import BaseModel, Field

from app.eval.metrics import text_similarity
from app.llm.gateway import get_gateway
from app.llm.structured import structured_call
from app.llm.tiers import Tier

log = structlog.get_logger("eval.judge")


class RootCauseVerdict(BaseModel):
    """Judge's score for how well an AI root cause matches the expert's true root cause."""

    score: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


_SYSTEM = (
    "You are a strict evaluator. Score how well the AI's identified ROOT CAUSE matches the "
    "expert's true root cause for the question, from 0.0 (wrong or missing) to 1.0 (same "
    "underlying cause). Judge meaning, not wording; give partial credit for partial causes."
)
_USER = "Question: {question}\n\nAI root cause: {ai}\n\nExpert (true) root cause: {expected}"


async def judge_root_cause(
    ai_root_cause: str | None,
    expected_root_cause: str | None,
    question: str = "",
) -> float:
    """Return a 0..1 root-cause match score from the LLM judge (embedding fallback on error)."""
    ai = (ai_root_cause or "").strip()
    expected = (expected_root_cause or "").strip()
    if not ai or not expected:
        return 0.0
    try:
        verdict = await structured_call(
            get_gateway().get_llm(Tier.SMART),
            _SYSTEM,
            _USER.format(question=question, ai=ai, expected=expected),
            RootCauseVerdict,
        )
        return round(max(0.0, min(1.0, verdict.score)), 4)
    except (ValueError, KeyError) as exc:
        log.warning("root_cause_judge_fallback", error=str(exc))
        return text_similarity(ai, expected)
