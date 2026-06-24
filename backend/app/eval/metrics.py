"""Pure metric functions for the eval harness (no LLM, no DB).

Scores are embedding-based where text comparison is needed (offline, deterministic, no
Groq tokens). Targets mirror the PDF Success Criteria. See docs/EVALUATION.md.
"""

import math

from app.rag.embeddings import embed_documents

# PDF Success Criteria targets.
TARGET_SIMILARITY = 0.75
TARGET_ROOT_CAUSE = 0.70
TARGET_COVERAGE = 0.80
TARGET_IMPROVEMENT = 0.20  # ≥20% relative increase in composite accuracy, V1 -> V2
TARGET_RESPONSE_S = 15.0
TARGET_SCENARIO_COVERAGE = 1.0


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two vectors, clamped to [0, 1]."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))


def text_similarity(a: str, b: str) -> float:
    """Embedding cosine similarity between two texts (0 if either is empty)."""
    a, b = (a or "").strip(), (b or "").strip()
    if not a or not b:
        return 0.0
    va, vb = embed_documents([a, b])
    return round(cosine(va, vb), 4)


def evidence_coverage(expected_refs: list[str], evidence_ids: set[str]) -> float:
    """Fraction of expected source refs present in the answer's evidence identifiers."""
    expected = {r.strip().lower() for r in expected_refs if r.strip()}
    if not expected:
        return 1.0
    covered = expected & {e.lower() for e in evidence_ids}
    return round(len(covered) / len(expected), 4)


def composite_accuracy(similarity: float, root_cause: float, coverage: float) -> float:
    """Mean of the three quality scores — a single 'accuracy' number per version."""
    return round((similarity + root_cause + coverage) / 3, 4)


def improvement(v1_composite: float, v2_composite: float) -> float:
    """Relative increase in composite accuracy from V1 to V2 (0.20 == +20%)."""
    if v1_composite == 0:
        return 1.0 if v2_composite > 0 else 0.0
    return round((v2_composite - v1_composite) / v1_composite, 4)
