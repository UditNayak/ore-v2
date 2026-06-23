"""The LangGraph: planner -> agentic investigator loop -> reasoner.

START -> planner -> investigator --(insufficient & budget left)--> investigator
                          |--(sufficient | max iters | sources exhausted)--> reasoner -> END
"""

from functools import lru_cache
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.nodes.investigator import investigator
from app.agents.nodes.planner import planner
from app.agents.nodes.reasoner import reasoner
from app.agents.state import GraphState
from app.core.config import get_settings

_INVESTIGATE = "investigator"
_REASON = "reasoner"


def route_after_investigation(state: GraphState) -> str:
    """Decide whether to loop the Investigator again or move on to the Reasoner.

    Pure function (no I/O) so the loop control is directly testable.
    """
    if state.sufficient:
        return _REASON
    if state.iterations >= get_settings().retrieval_max_iters:
        return _REASON
    remaining = [s for s in state.sources_to_check if s not in state.queried_sources]
    if not remaining:
        return _REASON
    return _INVESTIGATE


def build_graph() -> Any:
    """Wire and compile the V1 reasoning graph."""
    graph = StateGraph(GraphState)
    graph.add_node("planner", planner)
    graph.add_node(_INVESTIGATE, investigator)
    graph.add_node(_REASON, reasoner)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", _INVESTIGATE)
    graph.add_conditional_edges(
        _INVESTIGATE,
        route_after_investigation,
        {_INVESTIGATE: _INVESTIGATE, _REASON: _REASON},
    )
    graph.add_edge(_REASON, END)
    return graph.compile()


@lru_cache
def get_graph() -> Any:
    """Process-wide compiled graph (stateless; per-request data flows via config + state)."""
    return build_graph()
