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

    # Database (Phase 2). Async DSN used by the app; Alembic derives a sync DSN from it.
    database_url: str = "postgresql+asyncpg://ore:ore@db:5432/ore"

    # RAG / embeddings (Phase 2). EMBEDDING_DIM must match the model AND the pgvector column.
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    rag_top_k: int = 5
    seed_path: str = "app/data/seed"
    qa_scenarios_path: str = "app/data/qa_scenarios.json"

    # Agentic retrieval loop (Phase 3).
    retrieval_max_iters: int = 3
    rag_min_score: float = 0.3  # min cosine similarity for a doc chunk to count as evidence

    # Guardrails (Phase 3).
    confidence_threshold: float = 0.35  # below this, the answer is flagged low-confidence

    # Learning loop (Phase 4).
    learning_top_k: int = 3
    learning_min_score: float = 0.3  # min similarity for a past lesson to be injected

    # Observability (Phase 7) — LangSmith tracing of the graph + LLM calls (env-gated).
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "ore"
    langsmith_endpoint: str = "https://api.smith.langchain.com"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (one read of the environment per process)."""
    return Settings()
