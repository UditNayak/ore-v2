"""FastAPI application entrypoint.

Later phases extend the lifespan to run migrations and seed the synthetic dataset.
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, metrics, models, questions, scenarios
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.observability import configure_observability
from app.db.migrate import run_migrations
from app.db.seed import seed_if_empty
from app.db.session import SessionLocal

settings = get_settings()
configure_logging(settings.log_level)
configure_observability()
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """On startup: apply migrations (sync, off the event loop) then seed the corpus."""
    log.info("startup", app=settings.app_name, environment=settings.environment)
    await asyncio.to_thread(run_migrations)
    async with SessionLocal() as session:
        seeded = await seed_if_empty(session)
    log.info("ready", seeded=seeded)
    yield
    log.info("shutdown")


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

# Permissive CORS in development so the Vite dev server can call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(questions.router)
app.include_router(metrics.router)
app.include_router(scenarios.router)
app.include_router(models.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Friendly root pointing at the docs."""
    return {"service": "ore-backend", "docs": "/docs"}
