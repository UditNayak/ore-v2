"""Reasoning service — orchestrate the LangGraph run and persist the V1 answer.

Keeps the agent graph (pure reasoning) separate from persistence (this layer): the graph
returns state; the service writes the Question, AIAnswer, and AnswerEvidence rows.
"""

from typing import Any, cast

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.graph import get_graph
from app.agents.state import GraphState
from app.core.enums import QuestionStatus
from app.db.models import AIAnswer, AnswerEvidence, Question
from app.llm.gateway import get_gateway

log = structlog.get_logger("service.reasoning")


def _as_state(result: Any) -> GraphState:
    """LangGraph may return the state model or a plain mapping; normalize to GraphState."""
    return result if isinstance(result, GraphState) else GraphState(**result)


async def answer_question(
    session: AsyncSession,
    text: str,
    *,
    asker: str | None = None,
    channel: str | None = None,
) -> int:
    """Run the V1 reasoning graph for a new question and persist it. Returns the AIAnswer id."""
    question = Question(text=text, asker=asker, channel=channel, status=QuestionStatus.NEW.value)
    session.add(question)
    await session.flush()  # assign question.id

    initial = GraphState(question=text, question_id=question.id, version=1)
    result = await get_graph().ainvoke(
        initial, config={"configurable": {"session": session, "gateway": get_gateway()}}
    )
    final = _as_state(result)

    question.question_type = final.question_type
    question.status = QuestionStatus.ANSWERED_V1.value

    answer = AIAnswer(
        question_id=question.id,
        version=1,
        answer_text=final.answer_text or "",
        root_cause=final.root_cause,
        confidence=final.confidence,
        reasoning_trace=final.reasoning_trace,
        model_info={
            "question_type": final.question_type,
            "refused": final.refused,
            "refusal_reason": final.refusal_reason,
            "cited_source_refs": final.cited_source_refs,
            "iterations": final.iterations,
        },
    )
    session.add(answer)
    await session.flush()

    for ev in final.evidence:
        session.add(
            AnswerEvidence(
                ai_answer_id=answer.id,
                source_type=ev.source_type.value,
                source_ref=ev.source_ref,
                title=ev.title,
                snippet=ev.snippet,
                score=ev.score,
            )
        )
    await session.commit()
    log.info("answered_v1", question_id=question.id, answer_id=answer.id, refused=final.refused)
    return answer.id


async def get_answer(session: AsyncSession, answer_id: int) -> AIAnswer | None:
    """Load an AIAnswer with its evidence and question eagerly."""
    stmt = (
        select(AIAnswer)
        .where(AIAnswer.id == answer_id)
        .options(selectinload(AIAnswer.evidence), selectinload(AIAnswer.question))
    )
    return cast("AIAnswer | None", await session.scalar(stmt))
