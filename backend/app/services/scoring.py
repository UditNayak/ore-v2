"""Score an AI answer against a human answer (live, per-question).

Reuses the embedding-based metrics from the eval harness so the UI can show the same
quality numbers (similarity, root-cause match, evidence coverage) the eval reports.
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AIAnswer, HumanAnswer, SlackMessage
from app.eval import metrics


async def evidence_ids(session: AsyncSession, answer: AIAnswer) -> set[str]:
    """Stable identifiers for an answer's evidence (incl. slack thread ids)."""
    ids: set[str] = set()
    for ev in answer.evidence:
        ids.add(ev.source_ref)
        if ev.source_type == "slack" and ev.source_ref.isdigit():
            msg = await session.get(SlackMessage, int(ev.source_ref))
            if msg:
                ids.add(msg.thread_id)
    return ids


async def score_answer(
    session: AsyncSession, answer: AIAnswer, human: HumanAnswer
) -> dict[str, Any]:
    """Compute similarity / root-cause / coverage of `answer` vs the human ground truth.

    Coverage is None unless the expert declared `expected_sources`; root-cause is None unless
    the expert gave a root cause. Composite is the mean of whatever is present.
    """
    similarity = metrics.text_similarity(answer.answer_text, human.answer_text)
    root_cause = (
        metrics.text_similarity(answer.root_cause or "", human.root_cause)
        if human.root_cause
        else None
    )
    coverage = (
        metrics.evidence_coverage(human.expected_sources, await evidence_ids(session, answer))
        if human.expected_sources
        else None
    )
    present = [v for v in (similarity, root_cause, coverage) if v is not None]
    composite = round(sum(present) / len(present), 4) if present else 0.0
    return {
        "similarity": similarity,
        "root_cause": root_cause,
        "coverage": coverage,
        "composite": composite,
    }
