"""Critic — gap analysis of the AI's V1 answer against the human expert's ground truth.

Runs once when a human answer arrives (smart tier). Its structured output becomes a
learning event. This is the source of the V1 -> V2 improvement signal.
"""

import structlog

from app.agents.schemas import CriticOutput
from app.llm.gateway import LLMGateway
from app.llm.structured import structured_call
from app.llm.tiers import Tier

log = structlog.get_logger("learning.critic")

_SYSTEM = (
    "You are the Critic. Compare the AI's answer to the human expert's ground-truth answer and "
    "identify exactly what the AI got wrong or missed. Be specific and actionable: name the "
    "reasoning step it skipped, the correct root cause if it differs, and any source_ref the "
    "expert relied on that the AI did not cite. Produce a concise lesson to apply next time."
)
_USER = (
    "Question:\n{question}\n\n"
    "AI answer (V1):\n{ai_answer}\n"
    "AI root cause: {ai_root_cause}\n"
    "AI cited sources: {ai_sources}\n\n"
    "Human expert answer (ground truth):\n{human_answer}\n"
    "Human root cause: {human_root_cause}"
)


async def run_critic(
    gateway: LLMGateway,
    *,
    question: str,
    ai_answer: str,
    ai_root_cause: str | None,
    ai_sources: list[str],
    human_answer: str,
    human_root_cause: str | None,
) -> CriticOutput:
    """Produce a structured gap analysis (lesson) comparing V1 to the human answer."""
    try:
        out = await structured_call(
            gateway.get_llm(Tier.SMART),
            _SYSTEM,
            _USER.format(
                question=question,
                ai_answer=ai_answer,
                ai_root_cause=ai_root_cause or "(none)",
                ai_sources=", ".join(ai_sources) or "(none)",
                human_answer=human_answer,
                human_root_cause=human_root_cause or "(none)",
            ),
            CriticOutput,
        )
    except (ValueError, KeyError) as exc:
        log.warning("critic_fallback", error=str(exc))
        out = CriticOutput(
            summary="Compare against the expert answer and cite the sources it used."
        )
    log.info("critiqued", summary=out.summary, missed_sources=out.missed_sources)
    return out
