"""Scenarios API — exposes seeded ground-truth so the UI can autoload an expert answer."""

from fastapi import APIRouter

from app.api.schemas import ScenarioView
from app.eval.scenarios import load_scenarios

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioView])
async def list_scenarios() -> list[ScenarioView]:
    """Return the seeded test scenarios (question + expert answer + expected sources)."""
    return [
        ScenarioView(
            id=s.id,
            question=s.question,
            expert_answer=s.expert_answer,
            expected_root_cause=s.expected_root_cause,
            expected_source_refs=s.expected_source_refs,
        )
        for s in load_scenarios()
    ]
