"""Provider-agnostic LLM gateway: tiers + automatic fallback over LiteLLM.

Agent code should depend only on `Tier` and `get_gateway().get_llm(tier)` — never on a
specific provider or model. See docs/decisions/0002-llm-gateway-multiprovider.md.
"""

from app.llm.gateway import LLMGateway, get_gateway
from app.llm.tiers import Tier

__all__ = ["LLMGateway", "Tier", "get_gateway"]
