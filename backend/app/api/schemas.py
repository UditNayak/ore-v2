"""API request/response models (decoupled from ORM models)."""

from typing import Any

from pydantic import BaseModel

from app.db.models import AIAnswer


class AskRequest(BaseModel):
    """Submit a question to the reasoning engine."""

    text: str
    asker: str | None = None
    channel: str | None = None


class EvidenceView(BaseModel):
    """One cited piece of evidence."""

    source_type: str
    source_ref: str
    title: str | None
    snippet: str
    score: float | None


class AnswerView(BaseModel):
    """A generated answer (V1/V2) with its reasoning, confidence, and evidence."""

    answer_id: int
    question_id: int
    question: str
    version: int
    question_type: str | None
    answer_text: str
    root_cause: str | None
    confidence: float
    reasoning_trace: list[Any]
    refused: bool
    refusal_reason: str | None
    cited_source_refs: list[str]
    evidence: list[EvidenceView]

    @classmethod
    def from_orm_answer(cls, answer: AIAnswer) -> "AnswerView":
        """Build the view from an AIAnswer (with evidence + question loaded)."""
        info = answer.model_info or {}
        return cls(
            answer_id=answer.id,
            question_id=answer.question_id,
            question=answer.question.text,
            version=answer.version,
            question_type=info.get("question_type"),
            answer_text=answer.answer_text,
            root_cause=answer.root_cause,
            confidence=answer.confidence,
            reasoning_trace=answer.reasoning_trace,
            refused=bool(info.get("refused", False)),
            refusal_reason=info.get("refusal_reason"),
            cited_source_refs=info.get("cited_source_refs", []),
            evidence=[
                EvidenceView(
                    source_type=e.source_type,
                    source_ref=e.source_ref,
                    title=e.title,
                    snippet=e.snippet,
                    score=e.score,
                )
                for e in answer.evidence
            ],
        )
