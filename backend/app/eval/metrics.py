"""Pure metric functions for the eval harness (no LLM, no DB).

Scores are embedding-based where text comparison is needed (offline, deterministic, no
Groq tokens). Targets mirror the PDF Success Criteria. See docs/EVALUATION.md.
"""

import math
from typing import Any

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
    """Share of the remaining gap-to-perfect that V2 closes over V1 ("error reduction").

    improvement = (v2 - v1) / (1 - v1).

    Why this rather than the naive relative gain (v2 - v1) / v1: when the V1 baseline is already
    strong (often ~0.8 here), a small absolute gain is a *large* fraction of the headroom that was
    left. E.g. 0.80 -> 0.85 closes 25% of the remaining gap, but reads as only +6% relative-to-base.
    Gap-closed is the honest way to credit learning against a high baseline. Negative on regression;
    0 if V1 is already perfect.
    """
    gap = 1.0 - v1_composite
    if gap <= 0:
        return 0.0
    return round((v2_composite - v1_composite) / gap, 4)


def build_summary(results: list[dict[str, Any]], total: int) -> dict[str, Any]:
    """Aggregate per-question results into the dashboard summary shape (None-safe).

    Each result has v1/v2 score dicts (similarity/root_cause/coverage/composite, any may be None),
    an `improvement`, and a `response_s`. Used by both the eval harness and interactive completions.
    """
    n = len(results) or 1

    def avg(key: str, ver: str) -> float:
        return round(sum(float(r[ver].get(key) or 0.0) for r in results) / n, 4)

    response_times = [r["response_s"] for r in results if r.get("response_s") is not None]
    summary: dict[str, Any] = {
        "scenarios_run": len(results),
        "scenario_coverage": round(len(results) / total, 4) if total else 0.0,
        "v2_similarity": avg("similarity", "v2"),
        "v2_root_cause": avg("root_cause", "v2"),
        "v2_coverage": avg("coverage", "v2"),
        "avg_improvement": round(sum(r["improvement"] for r in results) / n, 4),
        "max_response_s": max(response_times) if response_times else None,
    }
    summary["targets"] = {
        "similarity": summary["v2_similarity"] >= TARGET_SIMILARITY,
        "root_cause": summary["v2_root_cause"] >= TARGET_ROOT_CAUSE,
        "coverage": summary["v2_coverage"] >= TARGET_COVERAGE,
        "improvement": summary["avg_improvement"] >= TARGET_IMPROVEMENT,
        "response_time": (
            (summary["max_response_s"] or 0) < TARGET_RESPONSE_S
            if summary["max_response_s"] is not None
            else None
        ),
        "scenario_coverage": summary["scenario_coverage"] >= TARGET_SCENARIO_COVERAGE,
    }
    return summary
