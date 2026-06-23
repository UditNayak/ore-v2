"""Structured outputs for each agent handoff (Pydantic — the rubric's typed handoffs).

Fields the LLM fills are intentionally permissive strings (LLM output is untrusted); the
nodes normalize/validate them against the controlled vocabularies in `app.core.enums`.
"""

from pydantic import BaseModel, Field


class PlannerOutput(BaseModel):
    """Planner decision: classify the question and pick which sources to investigate."""

    question_type: str = "other"
    sources: list[str] = Field(
        default_factory=list, description="Ordered source names to consult, most promising first."
    )
    rationale: str = ""


class SufficiencyVerdict(BaseModel):
    """Investigator's judgement after a retrieval step: do we have enough yet?"""

    sufficient: bool
    missing: str | None = Field(default=None, description="What is still missing, if anything.")
    refined_query: str | None = Field(
        default=None, description="A better query to try next, if not sufficient."
    )


class CriticOutput(BaseModel):
    """Gap analysis of the AI's V1 answer against the human expert's ground truth."""

    summary: str = Field(
        description="One-line lesson: what the AI should do differently next time."
    )
    missed_sources: list[str] = Field(
        default_factory=list,
        description="source_ref values the expert relied on that the AI missed.",
    )
    missed_reasoning: str | None = Field(
        default=None, description="A reasoning step or causal link the AI overlooked."
    )
    corrected_root_cause: str | None = Field(
        default=None, description="The correct root cause, if the AI's was wrong or incomplete."
    )


class ReasonerOutput(BaseModel):
    """The drafted answer with its reasoning, root cause, confidence, and citations."""

    answer_text: str
    root_cause: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_trace: list[str] = Field(description="Ordered reasoning steps leading to the answer.")
    cited_source_refs: list[str] = Field(
        default_factory=list, description="source_ref values (issue key / commit sha / id) cited."
    )
