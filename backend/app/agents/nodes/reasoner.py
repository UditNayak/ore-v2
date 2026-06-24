"""Reasoner node — synthesize evidence into the V1 answer (SMART tier).

Produces answer + reasoning trace + root cause + confidence, then applies guardrails:
no relevant evidence -> graceful refusal; low confidence or ungrounded citations -> flagged.
"""

from typing import Any

import structlog
from langchain_core.runnables import RunnableConfig

from app.agents.nodes.common import context, format_evidence
from app.agents.schemas import ReasonerOutput
from app.agents.state import GraphState
from app.core.config import get_settings
from app.core.guardrails import INSUFFICIENT_EVIDENCE_MESSAGE, evaluate_answer
from app.learning.injection import learning_block
from app.llm.structured import structured_call
from app.llm.tiers import Tier

log = structlog.get_logger("agent.reasoner")

_SYSTEM = (
    "You are the Reasoner in an organizational reasoning engine. Using ONLY the provided "
    "evidence, answer the question like a senior engineer: state the answer, the root cause, and "
    "your reasoning steps. In cited_source_refs, cite evidence using the bracketed id shown for "
    "each item (e.g. 'doc:8' or 'issue:NIM-412'). Be SELECTIVE: cite ONLY the few items that "
    "directly support your answer and root cause (typically 1-5) — do NOT list every item you were "
    "given; omit evidence you did not actually rely on. If the evidence does not support a "
    "confident answer, say so and give a low confidence. Never invent facts not in the evidence."
)
_USER = "Question: {question}\n\nEvidence:\n{evidence}"


async def reasoner(state: GraphState, config: RunnableConfig) -> dict[str, Any]:
    """Draft the answer and apply guardrails."""
    settings = get_settings()

    # Guardrail: no relevant evidence -> fail gracefully instead of guessing.
    if not state.evidence:
        log.info("refused", reason="no_evidence")
        return {
            "answer_text": INSUFFICIENT_EVIDENCE_MESSAGE,
            "confidence": 0.0,
            "refused": True,
            "refusal_reason": "no relevant evidence found",
            "reasoning_trace": ["No relevant evidence was found in the available sources."],
        }

    _, gateway = context(config)
    user = _USER.format(
        question=state.question, evidence=format_evidence(state.evidence)
    ) + learning_block(state.learning_context)
    try:
        out = await structured_call(gateway.get_llm(Tier.SMART), _SYSTEM, user, ReasonerOutput)
    except (ValueError, KeyError) as exc:
        log.warning("reasoner_failed", error=str(exc))
        return {
            "answer_text": INSUFFICIENT_EVIDENCE_MESSAGE,
            "confidence": 0.0,
            "refused": True,
            "refusal_reason": "could not produce a structured answer",
        }
    refused, reason = evaluate_answer(out, state.evidence, settings.confidence_threshold)
    log.info("reasoned", confidence=out.confidence, refused=refused, cites=out.cited_source_refs)

    return {
        "answer_text": out.answer_text,
        "root_cause": out.root_cause,
        "confidence": out.confidence,
        "reasoning_trace": out.reasoning_trace,
        "cited_source_refs": out.cited_source_refs,
        "refused": refused,
        "refusal_reason": reason,
    }
