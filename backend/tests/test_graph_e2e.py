"""End-to-end V1 reasoning against the live graph (uses Groq + the seeded corpus).

One live happy-path test (kept minimal to respect Groq free-tier token limits). The
refusal path is covered deterministically in test_nodes.py without an LLM call.
"""

from app.services.reasoning import answer_question, get_answer


async def test_v1_answer_for_release_delay(session) -> None:
    answer_id = await answer_question(session, "Why was release v2.4 delayed?")
    answer = await get_answer(session, answer_id)

    assert answer is not None
    assert answer.answer_text.strip()
    assert answer.evidence, "expected gathered evidence"
    assert answer.reasoning_trace, "expected a reasoning trace"
    assert 0.0 <= answer.confidence <= 1.0
    # Should be grounded in the v2.4 / billing storyline (lenient: LLM phrasing varies).
    blob = f"{answer.answer_text} {answer.root_cause or ''}".lower()
    refs = {e.source_ref for e in answer.evidence}
    assert "billing" in blob or "v2.4" in blob or "2.4" in blob or "NIM-412" in refs
