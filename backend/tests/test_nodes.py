"""Deterministic node behavior that must not depend on an LLM.

The Reasoner must refuse gracefully when there is no relevant evidence — this short-circuits
before any model call, so we can assert it directly (no Groq, no DB).
"""

from app.agents.nodes.reasoner import reasoner
from app.agents.state import GraphState


async def test_reasoner_refuses_without_evidence() -> None:
    state = GraphState(question="What is the boiling point of water on Mars?", evidence=[])
    result = await reasoner(state, config={})  # type: ignore[arg-type]

    assert result["refused"] is True
    assert result["confidence"] == 0.0
    assert result["answer_text"]  # a graceful message, not empty
