"""Observability wiring — env-gated LangSmith tracing. See ADR 0009.

LangChain/LangGraph emit traces to LangSmith automatically when the relevant environment
variables are set. We translate our typed settings into those env vars at startup, so
tracing is controlled from `.env` (LANGSMITH_TRACING=true + LANGSMITH_API_KEY) with no code
changes. When disabled, the system runs identically with only structured JSON logs.
"""

import os

import structlog

from app.core.config import get_settings

log = structlog.get_logger("observability")


def configure_observability() -> None:
    """Enable LangSmith tracing if configured; otherwise no-op (logs the decision)."""
    settings = get_settings()
    if not (settings.langsmith_tracing and settings.langsmith_api_key):
        log.info("langsmith_disabled", reason="not configured")
        return

    # LangChain reads these (both LANGSMITH_* and legacy LANGCHAIN_* are honored).
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    log.info("langsmith_enabled", project=settings.langsmith_project)
