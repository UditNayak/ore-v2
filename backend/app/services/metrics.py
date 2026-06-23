"""Dashboard metrics: read eval-run history, and record a point when a loop completes."""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EvalRun
from app.eval import metrics
from app.services.questions import load_question_detail
from app.services.scoring import score_answer

log = structlog.get_logger("service.metrics")


async def list_eval_runs(session: AsyncSession, limit: int = 50) -> list[EvalRun]:
    """Eval runs in chronological order (oldest first) for trend charts."""
    runs = (
        (await session.execute(select(EvalRun).order_by(EvalRun.id.desc()).limit(limit)))
        .scalars()
        .all()
    )
    return list(reversed(runs))


async def record_question_run(session: AsyncSession, question_id: int) -> int | None:
    """Record a Dashboard data point for a completed loop (V1 + expert answer + V2).

    No-op (returns None) unless V1, V2, and a human answer all exist. Reuses the same scoring +
    summary shape as the eval harness, so interactive completions show on the Dashboard.
    """
    detail = await load_question_detail(session, question_id)
    if detail is None or detail.human_answer is None:
        return None
    v1 = next((a for a in detail.ai_answers if a.version == 1), None)
    v2 = next((a for a in reversed(detail.ai_answers) if a.version >= 2), None)
    if v1 is None or v2 is None:
        return None

    human = detail.human_answer
    text = detail.question.text
    v1_scores = await score_answer(session, v1, human, question_text=text)
    v2_scores = await score_answer(session, v2, human, question_text=text)
    result = {
        "id": str(question_id),
        "question": text,
        "v1": v1_scores,
        "v2": v2_scores,
        "improvement": metrics.improvement(v1_scores["composite"], v2_scores["composite"]),
        "response_s": (v1.model_info or {}).get("elapsed_s"),
    }
    summary = metrics.build_summary([result], total=1)
    summary["source"] = "interactive"
    summary["question"] = text

    run = EvalRun(summary=summary, results=[result])
    session.add(run)
    await session.commit()
    log.info("recorded_question_run", question_id=question_id, improvement=result["improvement"])
    return run.id
