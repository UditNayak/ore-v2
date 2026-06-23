"""Eval metric functions — pure, no LLM (embeddings run on the cached fastembed model)."""

from app.eval.metrics import (
    composite_accuracy,
    cosine,
    evidence_coverage,
    improvement,
    text_similarity,
)


def test_cosine_basic() -> None:
    assert cosine([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_text_similarity_identical_is_high() -> None:
    text = "the release was delayed by a failing integration test"
    assert text_similarity(text, text) > 0.95


def test_text_similarity_unrelated_is_lower_than_identical() -> None:
    base = "checkout latency spike from db pool exhaustion"
    related = text_similarity(base, "the database connection pool was exhausted")
    unrelated = text_similarity(base, "the cafeteria menu changed on Tuesday")
    assert related > unrelated


def test_text_similarity_empty_is_zero() -> None:
    assert text_similarity("", "something") == 0.0


def test_evidence_coverage_full_partial_empty() -> None:
    assert evidence_coverage(["NIM-412", "a1b2c3d"], {"nim-412", "a1b2c3d"}) == 1.0
    assert evidence_coverage(["NIM-412", "t-rel-1"], {"nim-412"}) == 0.5
    assert evidence_coverage([], {"anything"}) == 1.0  # nothing required


def test_evidence_coverage_matches_slack_thread() -> None:
    # thread id supplied via evidence_ids (runner maps slack msg -> thread)
    assert evidence_coverage(["t-rel-1"], {"t-rel-1", "16"}) == 1.0


def test_composite_and_improvement() -> None:
    assert composite_accuracy(0.9, 0.6, 0.6) == 0.7
    # gap-closed: (v2 - v1) / (1 - v1)
    assert improvement(0.5, 0.6) == 0.2  # 0.1 / 0.5
    assert improvement(0.8, 0.85) == 0.25  # high baseline → 0.05 / 0.2
    assert improvement(0.9, 0.9) == 0.0  # no change
    assert improvement(1.0, 1.0) == 0.0  # already perfect → no headroom
