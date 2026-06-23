"""Investigator node — one step of the agentic retrieval loop (ADR 0007).

Each invocation queries the next planned source, filters for relevance, accumulates
evidence, then judges sufficiency (CHEAP tier). The graph's conditional edge decides
whether to loop again, switch source, or stop — `k` and source order are decisions, not
constants, bounded by a max-iterations cap.
"""

from typing import Any

import structlog
from langchain_core.runnables import RunnableConfig

from app.agents.nodes.common import (
    SEARCHABLE_SOURCES,
    context,
    dedup_evidence,
    format_evidence_brief,
    run_tool,
)
from app.agents.schemas import SufficiencyVerdict
from app.agents.state import GraphState
from app.core.config import get_settings
from app.core.guardrails import filter_relevant
from app.llm.structured import structured_call
from app.llm.tiers import Tier

log = structlog.get_logger("agent.investigator")

_SYSTEM = (
    "You are the Investigator. Given a question and the evidence gathered so far, decide "
    "whether it is sufficient to answer confidently. If not, say what is missing and suggest a "
    "better search query. Be strict: vague or tangential evidence is NOT sufficient."
)
_USER = "Question: {question}\n\nEvidence so far:\n{evidence}"


async def investigator(state: GraphState, config: RunnableConfig) -> dict[str, Any]:
    """Query the next source, accumulate relevant evidence, and judge sufficiency."""
    session, gateway = context(config)
    settings = get_settings()
    query = state.current_query or state.question

    remaining = [s for s in state.sources_to_check if s not in state.queried_sources]
    if not remaining:
        return {"sufficient": True}

    source = remaining[0]
    new_evidence = await run_tool(session, source, query)
    relevant = filter_relevant(new_evidence, settings.rag_min_score)
    evidence = dedup_evidence(state.evidence + relevant)
    iterations = state.iterations + 1

    try:
        verdict = await structured_call(
            gateway.get_llm(Tier.CHEAP),
            _SYSTEM,
            _USER.format(question=state.question, evidence=format_evidence_brief(evidence)),
            SufficiencyVerdict,
        )
    except (ValueError, KeyError) as exc:
        # If the judge fails, don't stop early — let the loop exhaust sources / hit the cap.
        log.warning("sufficiency_fallback", error=str(exc))
        verdict = SufficiencyVerdict(sufficient=False)
    queried = [*state.queried_sources, source]

    # If the planned sources are now exhausted but evidence is still insufficient, broaden to any
    # source not yet consulted — an expert keeps looking rather than stopping at the first plan.
    # This recovers sources the (cheap-tier) Planner under-selected, improving evidence coverage.
    sources_to_check = state.sources_to_check
    if not verdict.sufficient and not [s for s in sources_to_check if s not in queried]:
        untried = [s for s in SEARCHABLE_SOURCES if s not in queried]
        if untried:
            sources_to_check = list(dict.fromkeys([*sources_to_check, *untried]))
            log.info("broadened_sources", added=untried)

    log.info(
        "investigated",
        source=source,
        new=len(relevant),
        total=len(evidence),
        iteration=iterations,
        sufficient=verdict.sufficient,
    )
    return {
        "evidence": evidence,
        "queried_sources": queried,
        "sources_to_check": sources_to_check,
        "iterations": iterations,
        "sufficient": verdict.sufficient,
        "missing": verdict.missing,
        "current_query": verdict.refined_query or query,
    }
