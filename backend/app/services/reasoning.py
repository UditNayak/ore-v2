"""Reasoning service — orchestrate the LangGraph run and persist an answer (V1 or V2).

Keeps the agent graph (pure reasoning) separate from persistence (this layer): the graph
returns state; the service writes the Question, AIAnswer, and AnswerEvidence rows. Before
each run it injects relevant past lessons (retrieved-memory) — empty on a fresh V1, populated
on a re-run after a learning event exists.
"""

import time
from typing import Any, cast

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.graph import get_graph
from app.agents.state import GraphState
from app.core.enums import QuestionStatus
from app.db.models import AIAnswer, AnswerEvidence, Question
from app.learning.store import retrieve_learning_context
from app.llm.gateway import get_gateway
from app.llm.tiers import Tier

log = structlog.get_logger("service.reasoning")


def _as_state(result: Any) -> GraphState:
    """LangGraph may return the state model or a plain mapping; normalize to GraphState."""
    return result if isinstance(result, GraphState) else GraphState(**result)


async def _run_and_persist(session: AsyncSession, question: Question, version: int) -> int:
    """Run the graph for `question` at the given version, injecting learning, and persist."""
    # Correlate every downstream node/LLM log line with this question + version.
    structlog.contextvars.bind_contextvars(question_id=question.id, version=version)
    try:
        return await _run_graph_and_persist(session, question, version)
    finally:
        structlog.contextvars.unbind_contextvars("question_id", "version")


async def _run_graph_and_persist(session: AsyncSession, question: Question, version: int) -> int:
    gateway = get_gateway()
    reasoner_model = gateway.primary_model(Tier.SMART)["model"]
    planner_model = gateway.primary_model(Tier.CHEAP)["model"]
    lessons = await retrieve_learning_context(session, question.text)
    initial = GraphState(
        question=question.text,
        question_id=question.id,
        version=version,
        learning_context=lessons,
    )
    started = time.monotonic()
    result = await get_graph().ainvoke(
        initial,
        config={
            "configurable": {"session": session, "gateway": gateway},
            # Correlate the LangSmith trace with this question + version (searchable in the UI).
            "run_name": f"ore-q{question.id}-v{version}",
            "tags": ["ore", f"q{question.id}", f"v{version}"],
            "metadata": {"question_id": question.id, "version": version},
        },
    )
    elapsed_s = round(time.monotonic() - started, 2)
    final = _as_state(result)

    question.question_type = final.question_type
    question.status = (
        QuestionStatus.ANSWERED_V2.value if version >= 2 else QuestionStatus.ANSWERED_V1.value
    )

    answer = AIAnswer(
        question_id=question.id,
        version=version,
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
            "learning_applied": len(lessons),
            "elapsed_s": elapsed_s,
            "reasoner_model": reasoner_model,
            "planner_model": planner_model,
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
    log.info(
        "answered",
        question_id=question.id,
        version=version,
        answer_id=answer.id,
        lessons=len(lessons),
    )
    return answer.id


async def answer_question(
    session: AsyncSession,
    text: str,
    *,
    asker: str | None = None,
    channel: str | None = None,
) -> int:
    """Create a new question and produce its V1 answer. Returns the AIAnswer id."""
    question = Question(text=text, asker=asker, channel=channel, status=QuestionStatus.NEW.value)
    session.add(question)
    await session.flush()  # assign question.id
    return await _run_and_persist(session, question, version=1)


async def rerun_question(session: AsyncSession, question_id: int) -> int:
    """Re-run an existing question to produce the next version (e.g. V2) with injected memory."""
    question = await session.get(Question, question_id)
    if question is None:
        raise ValueError(f"question {question_id} not found")
    highest = await session.scalar(
        select(func.coalesce(func.max(AIAnswer.version), 0)).where(
            AIAnswer.question_id == question_id
        )
    )
    return await _run_and_persist(session, question, version=(highest or 0) + 1)


async def get_answer(session: AsyncSession, answer_id: int) -> AIAnswer | None:
    """Load an AIAnswer with its evidence and question eagerly."""
    stmt = (
        select(AIAnswer)
        .where(AIAnswer.id == answer_id)
        .options(selectinload(AIAnswer.evidence), selectinload(AIAnswer.question))
    )
    return cast("AIAnswer | None", await session.scalar(stmt))
