"""Reset runtime data for a fresh start — keeps the seeded knowledge corpus.

Deletes all questions (and their AI/human answers + evidence, via cascade), all learning
events (lessons), and all evaluation runs. The corpus (documents, issues, slack, commits)
is left intact, so you don't need to re-seed.

Run:  python -m app.db.reset
"""

import asyncio

import structlog
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EvalRun, LearningEvent, Question
from app.db.session import SessionLocal

log = structlog.get_logger("reset")


async def reset_runtime(session: AsyncSession) -> None:
    """Clear questions, lessons, and eval runs (corpus untouched)."""
    # Deleting questions cascades to ai_answers, answer_evidence, human_answers, and
    # learning_events (FK question_id). EvalRun is standalone. Explicit order for clarity.
    for model in (EvalRun, LearningEvent, Question):
        await session.execute(delete(model))
    await session.commit()
    log.info("reset_done", kept="knowledge corpus (documents, issues, slack, commits)")


async def _main() -> None:
    async with SessionLocal() as session:
        await reset_runtime(session)


if __name__ == "__main__":
    asyncio.run(_main())
