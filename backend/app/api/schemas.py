"""API request/response models (decoupled from ORM models)."""

from typing import Any

from pydantic import BaseModel

from app.db.models import AIAnswer, HumanAnswer, LearningEvent


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
    elapsed_s: float | None
    learning_applied: int
    evidence: list[EvidenceView]

    @classmethod
    def from_orm_answer(cls, answer: AIAnswer, question_text: str | None = None) -> "AnswerView":
        """Build the view from an AIAnswer; pass question_text to avoid a lazy load."""
        info = answer.model_info or {}
        return cls(
            answer_id=answer.id,
            question_id=answer.question_id,
            question=question_text if question_text is not None else answer.question.text,
            version=answer.version,
            question_type=info.get("question_type"),
            answer_text=answer.answer_text,
            root_cause=answer.root_cause,
            confidence=answer.confidence,
            reasoning_trace=answer.reasoning_trace,
            refused=bool(info.get("refused", False)),
            refusal_reason=info.get("refusal_reason"),
            cited_source_refs=info.get("cited_source_refs", []),
            elapsed_s=info.get("elapsed_s"),
            learning_applied=int(info.get("learning_applied", 0)),
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


class HumanAnswerRequest(BaseModel):
    """Expert ground-truth answer (the HITL step)."""

    answer_text: str
    root_cause: str | None = None
    expert_name: str | None = None


class HumanAnswerView(BaseModel):
    """A recorded expert answer."""

    answer_text: str
    root_cause: str | None
    expert_name: str | None

    @classmethod
    def from_model(cls, ha: HumanAnswer) -> "HumanAnswerView":
        return cls(answer_text=ha.answer_text, root_cause=ha.root_cause, expert_name=ha.expert_name)


class LearningEventView(BaseModel):
    """The gap analysis captured from comparing V1 to the expert answer."""

    id: int
    summary: str
    missed_sources: list[str]
    missed_reasoning: str | None
    corrected_root_cause: str | None

    @classmethod
    def from_model(cls, ev: LearningEvent) -> "LearningEventView":
        return cls(
            id=ev.id,
            summary=ev.summary,
            missed_sources=ev.missed_sources,
            missed_reasoning=ev.missed_reasoning,
            corrected_root_cause=ev.corrected_root_cause,
        )


class QuestionDetailView(BaseModel):
    """Everything about one question's learning loop: V1, expert answer, lesson, V2."""

    id: int
    text: str
    status: str
    question_type: str | None
    v1: AnswerView | None
    v2: AnswerView | None
    human_answer: HumanAnswerView | None
    learning_event: LearningEventView | None
