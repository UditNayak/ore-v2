"""Metrics API — eval-run history for the dashboard trends."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import EvalRunView
from app.db.session import get_session
from app.services.metrics import list_eval_runs

router = APIRouter(prefix="/metrics", tags=["metrics"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/eval-runs", response_model=list[EvalRunView])
async def eval_runs(session: SessionDep) -> list[EvalRunView]:
    """Aggregate summaries of past eval runs (oldest first) for trend charts."""
    runs = await list_eval_runs(session)
    return [
        EvalRunView(id=r.id, created_at=r.created_at.isoformat(), summary=r.summary) for r in runs
    ]
