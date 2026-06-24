"""Read eval-run history for the dashboard trends."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EvalRun


async def list_eval_runs(session: AsyncSession, limit: int = 50) -> list[EvalRun]:
    """Eval runs in chronological order (oldest first) for trend charts."""
    runs = (
        (await session.execute(select(EvalRun).order_by(EvalRun.id.desc()).limit(limit)))
        .scalars()
        .all()
    )
    return list(reversed(runs))
