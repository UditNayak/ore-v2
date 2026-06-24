"""Assemble the full learning-loop view of a question (V1, expert answer, lesson, V2)."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AIAnswer, HumanAnswer, LearningEvent, Question


@dataclass
class QuestionDetail:
    """Loaded ORM parts for one question's learning loop."""

    question: Question
    ai_answers: list[AIAnswer]  # ordered by version
    human_answer: HumanAnswer | None
    learning_event: LearningEvent | None


async def load_question_detail(session: AsyncSession, question_id: int) -> QuestionDetail | None:
    """Load a question with its answers + evidence, latest expert answer, and latest lesson."""
    question = await session.scalar(
        select(Question)
        .where(Question.id == question_id)
        .options(
            selectinload(Question.ai_answers).selectinload(AIAnswer.evidence),
            selectinload(Question.human_answers),
        )
    )
    if question is None:
        return None

    ai_answers = sorted(question.ai_answers, key=lambda a: a.version)
    human_answer = max(question.human_answers, key=lambda h: h.id, default=None)
    learning_event = await session.scalar(
        select(LearningEvent)
        .where(LearningEvent.question_id == question_id)
        .order_by(LearningEvent.id.desc())
        .limit(1)
    )
    return QuestionDetail(
        question=question,
        ai_answers=ai_answers,
        human_answer=human_answer,
        learning_event=learning_event,
    )


async def list_recent_questions(
    session: AsyncSession, limit: int = 50
) -> list[tuple[Question, int]]:
    """Most-recent questions with their AI-answer count (for the feed)."""
    questions = (
        (
            await session.execute(
                select(Question)
                .order_by(Question.id.desc())
                .limit(limit)
                .options(selectinload(Question.ai_answers))
            )
        )
        .scalars()
        .all()
    )
    return [(q, len(q.ai_answers)) for q in questions]
