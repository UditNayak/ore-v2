"""Provider-agnostic structured output.

`with_structured_output` depends on tool-calling support that varies by provider and is
not available on a fallback-composed runnable. Instead we prompt for JSON and parse it,
which works uniformly across every model the gateway can return (and across fallbacks).
"""

import json

import structlog
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import Runnable, RunnableConfig
from pydantic import BaseModel

from app.llm.metrics import LLMMetricsCallback

log = structlog.get_logger("llm")

_CALLBACKS: list[BaseCallbackHandler] = [LLMMetricsCallback()]


def _extract_json(text: str) -> str:
    """Pull the JSON object out of a model reply (tolerating code fences / prose)."""
    cleaned = text.strip()
    if "```" in cleaned:
        # take the content of the first fenced block
        parts = cleaned.split("```")
        cleaned = parts[1] if len(parts) > 1 else cleaned
        if cleaned.lstrip().lower().startswith("json"):
            cleaned = cleaned.lstrip()[4:]
    start, end = cleaned.find("{"), cleaned.rfind("}")
    return cleaned[start : end + 1] if start != -1 and end != -1 else cleaned


async def structured_call[T: BaseModel](
    llm: Runnable[object, object],
    system: str,
    user: str,
    schema: type[T],
) -> T:
    """Invoke `llm` and parse its reply into `schema` (Pydantic)."""
    parser: PydanticOutputParser[T] = PydanticOutputParser(pydantic_object=schema)
    prompt = f"{user}\n\n{parser.get_format_instructions()}"
    config: RunnableConfig = {"callbacks": _CALLBACKS}
    reply = await llm.ainvoke(
        [SystemMessage(content=system), HumanMessage(content=prompt)], config=config
    )
    content = getattr(reply, "content", reply)
    text = content if isinstance(content, str) else str(content)
    try:
        return schema.model_validate_json(_extract_json(text))
    except (json.JSONDecodeError, ValueError) as exc:
        log.warning("structured_parse_failed", schema=schema.__name__, error=str(exc))
        raise
