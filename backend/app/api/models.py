"""Models API — which model each agent/component uses (from config/llm.yaml)."""

from fastapi import APIRouter

from app.api.schemas import AgentModelView, ModelsView
from app.llm.gateway import get_gateway
from app.llm.tiers import Tier

router = APIRouter(tags=["models"])

# Which tier each agent runs on.
_AGENTS = [
    ("Planner", Tier.CHEAP),
    ("Investigator", Tier.CHEAP),
    ("Reasoner", Tier.SMART),
    ("Critic", Tier.SMART),
]


@router.get("/models", response_model=ModelsView)
async def list_models() -> ModelsView:
    """Return the primary model behind each tier and agent."""
    gw = get_gateway()
    cheap = gw.primary_model(Tier.CHEAP)
    smart = gw.primary_model(Tier.SMART)
    agents = [
        AgentModelView(
            agent=name,
            tier=tier.value,
            **(gw.primary_model(tier)),
        )
        for name, tier in _AGENTS
    ]
    return ModelsView(cheap=cheap["model"], smart=smart["model"], agents=agents)
