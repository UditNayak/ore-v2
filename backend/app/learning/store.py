"""Learning-event persistence and retrieval (the 'memory' in retrieved-memory injection)."""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.schemas import CriticOutput
from app.core.config import get_settings
from app.db.models import LearningEvent
from app.learning.injection import format_learning_event
from app.rag.embeddings import embed_documents, embed_query

log = structlog.get_logger("learning.store")


def _embedding_text(question: str, critic: CriticOutput) -> str:
    """Text used to embed a learning event for later similarity retrieval."""
    bits = [
        question,
        critic.summary,
        critic.missed_reasoning or "",
        critic.corrected_root_cause or "",
    ]
    return "\n".join(b for b in bits if b)


async def create_learning_event(
    session: AsyncSession,
    *,
    question_id: int,
    question_text: str,
    ai_answer_id: int | None,
    critic: CriticOutput,
) -> LearningEvent:
    """Persist a learning event with its embedding (caller commits)."""
    embedding = embed_documents([_embedding_text(question_text, critic)])[0]
    event = LearningEvent(
        question_id=question_id,
        ai_answer_id=ai_answer_id,
        summary=critic.summary,
        missed_sources=critic.missed_sources,
        missed_reasoning=critic.missed_reasoning,
        corrected_root_cause=critic.corrected_root_cause,
        embedding=embedding,
    )
    session.add(event)
    return event


async def retrieve_learning_context(session: AsyncSession, question_text: str) -> list[str]:
    """Return formatted lessons from past events similar to the question (above threshold)."""
    settings = get_settings()
    query_vec = embed_query(question_text)
    distance = LearningEvent.embedding.cosine_distance(query_vec).label("distance")
    stmt = select(LearningEvent, distance).order_by(distance).limit(settings.learning_top_k)
    rows = (await session.execute(stmt)).all()

    lessons = [
        format_learning_event(event)
        for event, dist in rows
        if (1.0 - float(dist)) >= settings.learning_min_score
    ]
    if lessons:
        log.info("learning_injected", count=len(lessons))
    return lessons
