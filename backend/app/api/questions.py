"""Questions API — ask, capture the expert answer (HITL), re-run (V2), and inspect."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    AnswerMetricsView,
    AnswerView,
    AskRequest,
    HumanAnswerRequest,
    HumanAnswerView,
    LearningEventView,
    QuestionDetailView,
    QuestionListItem,
)
from app.db.models import AIAnswer
from app.db.session import get_session
from app.services.learning import get_learning_event, submit_human_answer
from app.services.metrics import record_question_run
from app.services.questions import list_recent_questions, load_question_detail
from app.services.reasoning import answer_question, get_answer, rerun_question
from app.services.scoring import evidence_ids, score_answer

router = APIRouter(prefix="/questions", tags=["questions"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def _answer_view(session: AsyncSession, answer_id: int) -> AnswerView:
    answer = await get_answer(session, answer_id)
    if answer is None:  # pragma: no cover
        raise HTTPException(status_code=500, detail="answer not found after creation")
    return AnswerView.from_orm_answer(answer)


@router.post("", response_model=AnswerView, status_code=201)
async def ask_question(payload: AskRequest, session: SessionDep) -> AnswerView:
    """Submit a question; runs the multi-agent graph and returns the V1 answer."""
    answer_id = await answer_question(
        session, payload.text, asker=payload.asker, channel=payload.channel
    )
    return await _answer_view(session, answer_id)


@router.get("", response_model=list[QuestionListItem])
async def list_questions(session: SessionDep) -> list[QuestionListItem]:
    """Recent questions (the feed)."""
    rows = await list_recent_questions(session)
    return [
        QuestionListItem(
            id=q.id,
            text=q.text,
            status=q.status,
            question_type=q.question_type,
            versions=versions,
        )
        for q, versions in rows
    ]


@router.post("/{question_id}/human-answer", response_model=LearningEventView, status_code=201)
async def add_human_answer(
    question_id: int, payload: HumanAnswerRequest, session: SessionDep
) -> LearningEventView:
    """Record the expert (ground-truth) answer and return the resulting gap analysis (lesson)."""
    try:
        event_id = await submit_human_answer(
            session,
            question_id,
            answer_text=payload.answer_text,
            root_cause=payload.root_cause,
            expert_name=payload.expert_name,
            expected_sources=payload.expected_sources,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    event = await get_learning_event(session, event_id)
    if event is None:  # pragma: no cover
        raise HTTPException(status_code=500, detail="learning event not found after creation")
    return LearningEventView.from_model(event)


@router.post("/{question_id}/rerun", response_model=AnswerView, status_code=201)
async def rerun(question_id: int, session: SessionDep) -> AnswerView:
    """Re-run the question with injected memory and return the improved (V2) answer."""
    try:
        answer_id = await rerun_question(session, question_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    # Record a Dashboard data point now that the loop (V1 -> expert -> V2) is complete.
    await record_question_run(session, question_id)
    return await _answer_view(session, answer_id)


@router.get("/{question_id}", response_model=QuestionDetailView)
async def read_question(question_id: int, session: SessionDep) -> QuestionDetailView:
    """Full learning-loop view of a question: V1, expert answer, lesson, and V2."""
    detail = await load_question_detail(session, question_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="question not found")

    text = detail.question.text
    v1 = next((a for a in detail.ai_answers if a.version == 1), None)
    v2 = next((a for a in reversed(detail.ai_answers) if a.version >= 2), None)
    human = detail.human_answer

    async def metrics_for(answer: AIAnswer | None) -> AnswerMetricsView | None:
        if answer is None or human is None:
            return None
        return AnswerMetricsView(**await score_answer(session, answer, human, question_text=text))

    # Deterministic gap: expert sources that V1's evidence did not cover.
    v1_missed_sources: list[str] = []
    if v1 is not None and human is not None and human.expected_sources:
        covered = {e.lower() for e in await evidence_ids(session, v1)}
        v1_missed_sources = [s for s in human.expected_sources if s.strip().lower() not in covered]

    return QuestionDetailView(
        id=detail.question.id,
        text=text,
        status=detail.question.status,
        question_type=detail.question.question_type,
        v1=AnswerView.from_orm_answer(v1, text) if v1 else None,
        v2=AnswerView.from_orm_answer(v2, text) if v2 else None,
        v1_metrics=await metrics_for(v1),
        v2_metrics=await metrics_for(v2),
        v1_missed_sources=v1_missed_sources,
        human_answer=HumanAnswerView.from_model(human) if human else None,
        learning_event=(
            LearningEventView.from_model(detail.learning_event) if detail.learning_event else None
        ),
    )


@router.get("/answers/{answer_id}", response_model=AnswerView)
async def read_answer(answer_id: int, session: SessionDep) -> AnswerView:
    """Fetch a previously generated answer by id."""
    answer = await get_answer(session, answer_id)
    if answer is None:
        raise HTTPException(status_code=404, detail="answer not found")
    return AnswerView.from_orm_answer(answer)
