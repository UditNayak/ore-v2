"""Learning loop — the memory mechanism that makes V2 better than V1.

Critical paths (no LLM): a learning event round-trips through pgvector and is retrieved for
a similar question, and the injection block is formatted correctly.
"""

from app.agents.schemas import CriticOutput
from app.db.models import LearningEvent, Question
from app.learning.injection import LEARNING_PREAMBLE, format_learning_event, learning_block
from app.learning.store import create_learning_event, retrieve_learning_context

DISTINCTIVE_Q = (
    "Why did the Zephyr-7 canary deployment to the Antarctica region roll back overnight?"
)


async def test_learning_event_roundtrip_and_retrieval(session) -> None:
    question = Question(text=DISTINCTIVE_Q)
    session.add(question)
    await session.flush()

    critic = CriticOutput(
        summary="Check the canary rollback logs and the region's feature-flag state.",
        missed_sources=["INC-999"],
        missed_reasoning="Rollback came from a failing canary health check, not a deploy bug.",
        corrected_root_cause="Canary health check failed due to a stale feature flag.",
    )
    await create_learning_event(
        session,
        question_id=question.id,
        question_text=DISTINCTIVE_Q,
        ai_answer_id=None,
        critic=critic,
    )
    await session.commit()

    lessons = await retrieve_learning_context(session, DISTINCTIVE_Q)
    assert any("canary rollback logs" in lesson for lesson in lessons)


def test_learning_block_empty_is_blank() -> None:
    assert learning_block([]) == ""


def test_learning_block_includes_preamble_and_lessons() -> None:
    block = learning_block(["- Lesson: do X"])
    assert LEARNING_PREAMBLE in block
    assert "do X" in block


def test_format_learning_event_renders_fields() -> None:
    event = LearningEvent(
        question_id=1,
        summary="Cite the postmortem.",
        missed_sources=["INC-87"],
        missed_reasoning="shared connection pool",
        corrected_root_cause="pool exhaustion",
        embedding=[0.0],
    )
    text = format_learning_event(event)
    assert "Cite the postmortem." in text
    assert "INC-87" in text
    assert "pool exhaustion" in text
