"""Planner node — classify the question and choose which sources to investigate.

Runs on the CHEAP tier (classification/routing is low-stakes). Its source choice is the
rubric's conditional routing into the rest of the graph.
"""

from typing import Any

import structlog
from langchain_core.runnables import RunnableConfig

from app.agents.nodes.common import SEARCHABLE_SOURCES, context
from app.agents.schemas import PlannerOutput
from app.agents.state import GraphState
from app.core.enums import QuestionType
from app.learning.injection import learning_block
from app.llm.structured import structured_call
from app.llm.tiers import Tier

log = structlog.get_logger("agent.planner")


def _normalize_question_type(value: str) -> str:
    """Coerce the LLM's question_type to a known value, defaulting to 'other'."""
    try:
        return QuestionType(value.strip().lower()).value
    except ValueError:
        return QuestionType.OTHER.value


_SYSTEM = (
    "You are the Planner in an organizational reasoning engine. Classify the user's question "
    "and decide which knowledge sources to investigate, most promising first.\n"
    f"Valid sources: {', '.join(SEARCHABLE_SOURCES)}.\n"
    "Guidance: incidents -> doc (postmortems) + slack + commit; release delays / blockers -> "
    "issue + slack; ownership -> doc + slack + commit; design rationale -> doc + slack."
)
_USER = "Question: {question}"


async def planner(state: GraphState, config: RunnableConfig) -> dict[str, Any]:
    """Set question_type and the ordered source list to investigate."""
    _, gateway = context(config)
    try:
        user = _USER.format(question=state.question) + learning_block(state.learning_context)
        out = await structured_call(gateway.get_llm(Tier.CHEAP), _SYSTEM, user, PlannerOutput)
        question_type = _normalize_question_type(out.question_type)
        picked = (s.strip().lower() for s in out.sources)
        sources = [s for s in picked if s in SEARCHABLE_SOURCES]
    except (ValueError, KeyError) as exc:
        log.warning("planner_fallback", error=str(exc))
        question_type, sources = QuestionType.OTHER.value, []

    # Fall back to consulting every source if the model picked none valid.
    if not sources:
        sources = list(SEARCHABLE_SOURCES)

    log.info("planned", question_type=question_type, sources=sources)
    return {
        "question_type": question_type,
        "sources_to_check": sources,
        "current_query": state.question,
    }
