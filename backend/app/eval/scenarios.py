"""Load the evaluation scenarios (question + expert ground truth) from JSON."""

import json
from pathlib import Path

from pydantic import BaseModel, Field

from app.core.config import get_settings


class CrossQuestion(BaseModel):
    q: str
    a: str


class Scenario(BaseModel):
    """One evaluation case: a question and its expert ground truth."""

    id: str
    question: str
    question_type: str | None = None
    expert_answer: str
    expected_root_cause: str | None = None
    expected_source_refs: list[str] = Field(default_factory=list)
    cross_questions: list[CrossQuestion] = Field(default_factory=list)


def load_scenarios() -> list[Scenario]:
    """Load and validate all scenarios from the configured path."""
    path = Path(get_settings().qa_scenarios_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Scenario.model_validate(item) for item in raw]
