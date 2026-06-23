"""Guardrails: keep the system honest. See ADR 0006.

These are pure functions so they are trivially testable and reusable across nodes:
- relevance filtering (don't treat low-similarity chunks as evidence),
- evidence grounding (answers must cite available sources),
- confidence thresholding (fail gracefully instead of guessing).
"""

from app.agents.schemas import ReasonerOutput
from app.core.enums import SourceType
from app.tools.schemas import Evidence

INSUFFICIENT_EVIDENCE_MESSAGE = (
    "I don't have enough evidence in the available sources to answer this confidently. "
    "Here's what would help: more specific details, or sources covering this topic."
)


def filter_relevant(evidence: list[Evidence], min_doc_score: float) -> list[Evidence]:
    """Drop evidence that isn't actually relevant.

    Semantic (doc) hits must clear a cosine-similarity floor; keyword hits already required
    a term match, so any positive score counts.
    """
    kept: list[Evidence] = []
    for e in evidence:
        score = e.score or 0.0
        if e.source_type == SourceType.DOC:
            if score >= min_doc_score:
                kept.append(e)
        elif score > 0.0:
            kept.append(e)
    return kept


def evaluate_answer(
    answer: ReasonerOutput,
    evidence: list[Evidence],
    confidence_threshold: float,
) -> tuple[bool, str | None]:
    """Return (refused, reason). Refuse on low confidence or ungrounded citations."""
    if answer.confidence < confidence_threshold:
        return True, f"confidence {answer.confidence:.2f} below {confidence_threshold:.2f}"

    # Accept either the bare ref ("NIM-412", "8") or the bracketed "type:ref" form ("doc:8")
    # the model is shown — so citation formatting can't trigger a false "ungrounded" refusal.
    available = {e.source_ref for e in evidence} | {
        f"{e.source_type}:{e.source_ref}" for e in evidence
    }
    if answer.cited_source_refs and not (set(answer.cited_source_refs) & available):
        return True, "answer cites no available source (ungrounded)"

    return False, None
