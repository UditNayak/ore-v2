"""Application settings, loaded from environment (and a local .env if present).

Phase 0 keeps this intentionally small; later phases add DB, LLM, and observability
settings as those subsystems land.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Organizational Reasoning Engine"
    environment: str = "development"
    log_level: str = "INFO"

    # LLM gateway (Phase 1). Provider keys are read by LiteLLM from the environment
    # (e.g. GROQ_API_KEY); we only need the path to the tier/provider config here.
    llm_config_path: str = "config/llm.yaml"

    # Populated in later phases; declared here so config stays one place.
    database_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (one read of the environment per process)."""
    return Settings()
