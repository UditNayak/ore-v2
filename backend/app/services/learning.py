"""Learning service — capture the human answer (HITL) and turn the gap into a learning event."""

from typing import cast

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import QuestionStatus
from app.db.models import AIAnswer, HumanAnswer, LearningEvent, Question
from app.learning.critic import run_critic
from app.learning.store import create_learning_event
from app.llm.gateway import get_gateway

log = structlog.get_logger("service.learning")


async def _latest_ai_answer(session: AsyncSession, question_id: int) -> AIAnswer | None:
    stmt = (
        select(AIAnswer)
        .where(AIAnswer.question_id == question_id)
        .order_by(AIAnswer.version.desc())
        .options(selectinload(AIAnswer.evidence))
        .limit(1)
    )
    return cast("AIAnswer | None", await session.scalar(stmt))


async def submit_human_answer(
    session: AsyncSession,
    question_id: int,
    *,
    answer_text: str,
    root_cause: str | None = None,
    expert_name: str | None = None,
) -> int:
    """Record the expert answer, run gap analysis, and persist a learning event.

    Returns the learning event id. This is the HITL step that drives V1 -> V2 improvement.
    """
    question = await session.get(Question, question_id)
    if question is None:
        raise ValueError(f"question {question_id} not found")

    session.add(
        HumanAnswer(
            question_id=question_id,
            answer_text=answer_text,
            root_cause=root_cause,
            expert_name=expert_name,
        )
    )

    ai_answer = await _latest_ai_answer(session, question_id)
    ai_sources = [e.source_ref for e in ai_answer.evidence] if ai_answer else []

    critic = await run_critic(
        get_gateway(),
        question=question.text,
        ai_answer=ai_answer.answer_text if ai_answer else "(no AI answer)",
        ai_root_cause=ai_answer.root_cause if ai_answer else None,
        ai_sources=ai_sources,
        human_answer=answer_text,
        human_root_cause=root_cause,
    )

    event = await create_learning_event(
        session,
        question_id=question_id,
        question_text=question.text,
        ai_answer_id=ai_answer.id if ai_answer else None,
        critic=critic,
    )
    question.status = QuestionStatus.LEARNED.value
    await session.commit()
    log.info("learned", question_id=question_id, learning_event_id=event.id)
    return event.id


async def get_learning_event(session: AsyncSession, event_id: int) -> LearningEvent | None:
    """Load a learning event by id."""
    return await session.get(LearningEvent, event_id)
