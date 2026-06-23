"""Live smoke test for the LLM gateway.

Calls both tiers against the configured provider (Groq in Phase 1) and prints the
replies plus the metrics emitted by the callback. Requires the relevant provider key
(e.g. GROQ_API_KEY) in the environment.

Run:  python -m app.llm.smoke
"""

import asyncio

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from app.core.logging import configure_logging
from app.llm.gateway import get_gateway
from app.llm.metrics import LLMMetricsCallback
from app.llm.tiers import Tier


async def main() -> None:
    configure_logging("INFO")
    gateway = get_gateway()
    callbacks: list[BaseCallbackHandler] = [LLMMetricsCallback()]
    config: RunnableConfig = {"callbacks": callbacks}

    for tier in (Tier.CHEAP, Tier.SMART):
        llm = gateway.get_llm(tier)
        reply = await llm.ainvoke(
            [HumanMessage(content="Reply with exactly three words: a friendly greeting.")],
            config=config,
        )
        print(f"[{tier.value}] -> {reply.content!r}")


if __name__ == "__main__":
    asyncio.run(main())
