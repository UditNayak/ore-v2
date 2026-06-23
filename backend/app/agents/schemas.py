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


class ReasonerOutput(BaseModel):
    """The drafted answer with its reasoning, root cause, confidence, and citations."""

    answer_text: str
    root_cause: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_trace: list[str] = Field(description="Ordered reasoning steps leading to the answer.")
    cited_source_refs: list[str] = Field(
        default_factory=list, description="source_ref values (issue key / commit sha / id) cited."
    )
