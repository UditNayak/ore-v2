"""The agentic-retrieval loop control — pure routing function (no I/O, no LLM)."""

from app.agents.graph import route_after_investigation
from app.agents.state import GraphState
from app.core.config import get_settings


def _state(**kw: object) -> GraphState:
    return GraphState(question="q", **kw)


def test_loops_when_insufficient_and_budget_remains() -> None:
    state = _state(
        sources_to_check=["doc", "issue", "slack"],
        queried_sources=["doc"],
        sufficient=False,
        iterations=1,
    )
    assert route_after_investigation(state) == "investigator"


def test_stops_when_sufficient() -> None:
    state = _state(sources_to_check=["doc", "issue"], queried_sources=["doc"], sufficient=True)
    assert route_after_investigation(state) == "reasoner"


def test_stops_at_max_iterations() -> None:
    max_iters = get_settings().retrieval_max_iters
    state = _state(
        sources_to_check=["doc", "issue", "slack", "commit"],
        queried_sources=["doc"],
        sufficient=False,
        iterations=max_iters,
    )
    assert route_after_investigation(state) == "reasoner"


def test_stops_when_all_sources_exhausted() -> None:
    state = _state(
        sources_to_check=["doc", "issue"],
        queried_sources=["doc", "issue"],
        sufficient=False,
        iterations=2,
    )
    assert route_after_investigation(state) == "reasoner"
