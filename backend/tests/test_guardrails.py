"""Guardrails — relevance filtering, confidence threshold, and grounding (pure functions)."""

from app.agents.schemas import ReasonerOutput
from app.core.enums import SourceType
from app.core.guardrails import evaluate_answer, filter_relevant
from app.tools.schemas import Evidence


def _ev(source_type: SourceType, ref: str, score: float | None) -> Evidence:
    return Evidence(source_type=source_type, source_ref=ref, snippet="x", score=score)


def test_filter_relevant_applies_doc_score_floor() -> None:
    evidence = [
        _ev(SourceType.DOC, "1", 0.5),  # keep (>= 0.3)
        _ev(SourceType.DOC, "2", 0.1),  # drop (< 0.3)
        _ev(SourceType.SLACK, "3", 0.4),  # keep (keyword, > 0)
        _ev(SourceType.COMMIT, "4", 0.0),  # drop (no match)
    ]
    kept = {e.source_ref for e in filter_relevant(evidence, min_doc_score=0.3)}
    assert kept == {"1", "3"}


def _answer(confidence: float, cited: list[str]) -> ReasonerOutput:
    return ReasonerOutput(
        answer_text="a", confidence=confidence, reasoning_trace=["s"], cited_source_refs=cited
    )


def test_refuses_on_low_confidence() -> None:
    refused, reason = evaluate_answer(_answer(0.1, ["NIM-412"]), [], confidence_threshold=0.35)
    assert refused and reason is not None


def test_refuses_when_citations_ungrounded() -> None:
    evidence = [_ev(SourceType.ISSUE, "NIM-412", 1.0)]
    refused, reason = evaluate_answer(
        _answer(0.9, ["NIM-999"]), evidence, confidence_threshold=0.35
    )
    assert refused and "ungrounded" in (reason or "")


def test_accepts_grounded_confident_answer() -> None:
    evidence = [_ev(SourceType.ISSUE, "NIM-412", 1.0)]
    refused, reason = evaluate_answer(
        _answer(0.9, ["NIM-412"]), evidence, confidence_threshold=0.35
    )
    assert not refused and reason is None
