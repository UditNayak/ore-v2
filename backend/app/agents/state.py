"""Shared LangGraph state threaded through every node (the rubric's shared state)."""

from pydantic import BaseModel, Field

from app.tools.schemas import Evidence


class GraphState(BaseModel):
    """Mutable state for one question's V1 reasoning run."""

    # Input
    question: str
    question_id: int | None = None
    version: int = 1

    # Retrieved-memory injection (Phase 4): lessons from past expert feedback, if any.
    learning_context: list[str] = Field(default_factory=list)

    # Planner output
    question_type: str | None = None
    sources_to_check: list[str] = Field(default_factory=list)

    # Investigator (agentic retrieval loop)
    current_query: str | None = None
    queried_sources: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    iterations: int = 0
    sufficient: bool = False
    missing: str | None = None

    # Reasoner output
    answer_text: str | None = None
    root_cause: str | None = None
    confidence: float = 0.0
    reasoning_trace: list[str] = Field(default_factory=list)
    cited_source_refs: list[str] = Field(default_factory=list)

    # Guardrail outcome
    refused: bool = False
    refusal_reason: str | None = None
