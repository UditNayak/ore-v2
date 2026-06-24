"""Run the evaluation harness: drive each scenario through V1 → expert → V2 and score it.

Reuses the real services (`answer_question`, `submit_human_answer`, `rerun_question`) so the
eval exercises the exact production path. Results are printed, written to `eval_results/`, and
persisted to the `eval_runs` table for trend tracking.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AIAnswer, EvalRun, LearningEvent
from app.db.session import SessionLocal
from app.eval import metrics
from app.eval.scenarios import Scenario, load_scenarios
from app.services.learning import submit_human_answer
from app.services.reasoning import answer_question, get_answer, rerun_question
from app.services.scoring import evidence_ids

log = structlog.get_logger("eval")

REPORT_DIR = Path("eval_results")


async def _score(session: AsyncSession, scenario: Scenario, answer: AIAnswer) -> dict[str, Any]:
    similarity = metrics.text_similarity(answer.answer_text, scenario.expert_answer)
    root_cause = (
        metrics.text_similarity(answer.root_cause or "", scenario.expected_root_cause)
        if scenario.expected_root_cause
        else 0.0
    )
    coverage = metrics.evidence_coverage(
        scenario.expected_source_refs, await evidence_ids(session, answer)
    )
    return {
        "similarity": similarity,
        "root_cause": root_cause,
        "coverage": coverage,
        "composite": metrics.composite_accuracy(similarity, root_cause, coverage),
        "confidence": answer.confidence,
        "refused": bool((answer.model_info or {}).get("refused")),
        "elapsed_s": (answer.model_info or {}).get("elapsed_s"),
    }


async def _run_scenario(session: AsyncSession, scenario: Scenario) -> dict[str, Any]:
    v1_id = await answer_question(session, scenario.question)
    v1 = await get_answer(session, v1_id)
    assert v1 is not None
    v1_score = await _score(session, scenario, v1)

    await submit_human_answer(
        session,
        v1.question_id,
        answer_text=scenario.expert_answer,
        root_cause=scenario.expected_root_cause,
        expert_name="eval",
        expected_sources=scenario.expected_source_refs,
    )
    v2_id = await rerun_question(session, v1.question_id)
    v2 = await get_answer(session, v2_id)
    assert v2 is not None
    v2_score = await _score(session, scenario, v2)

    return {
        "id": scenario.id,
        "question": scenario.question,
        "v1": v1_score,
        "v2": v2_score,
        "improvement": metrics.improvement(v1_score["composite"], v2_score["composite"]),
        "response_s": v1_score["elapsed_s"],
    }


def _aggregate(results: list[dict[str, Any]], total_scenarios: int) -> dict[str, Any]:
    n = len(results) or 1

    def avg(key: str, ver: str) -> float:
        return round(sum(float(r[ver][key]) for r in results) / n, 4)

    response_times = [r["response_s"] for r in results if r["response_s"] is not None]
    summary = {
        "scenarios_run": len(results),
        "scenario_coverage": round(len(results) / total_scenarios, 4) if total_scenarios else 0.0,
        "v2_similarity": avg("similarity", "v2"),
        "v2_root_cause": avg("root_cause", "v2"),
        "v2_coverage": avg("coverage", "v2"),
        "avg_improvement": round(sum(r["improvement"] for r in results) / n, 4),
        "max_response_s": max(response_times) if response_times else None,
    }
    summary["targets"] = {
        "similarity": _check(summary["v2_similarity"], metrics.TARGET_SIMILARITY),
        "root_cause": _check(summary["v2_root_cause"], metrics.TARGET_ROOT_CAUSE),
        "coverage": _check(summary["v2_coverage"], metrics.TARGET_COVERAGE),
        "improvement": _check(summary["avg_improvement"], metrics.TARGET_IMPROVEMENT),
        "response_time": (
            (summary["max_response_s"] or 0) < metrics.TARGET_RESPONSE_S
            if summary["max_response_s"] is not None
            else None
        ),
        "scenario_coverage": _check(summary["scenario_coverage"], metrics.TARGET_SCENARIO_COVERAGE),
    }
    return summary


def _check(value: float, target: float) -> bool:
    return value >= target


def _render_markdown(summary: dict[str, Any], results: list[dict[str, Any]]) -> str:
    t = summary["targets"]

    def row(name: str, value: Any, target: str, ok: Any) -> str:
        mark = "—" if ok is None else ("✅" if ok else "❌")
        return f"| {name} | {value} | {target} | {mark} |"

    lines = [
        "# Evaluation report",
        "",
        f"Scenarios run: {summary['scenarios_run']} "
        f"(coverage {summary['scenario_coverage'] * 100:.0f}%)",
        "",
        "| Metric | Value | Target | Pass |",
        "|---|---|---|---|",
        row("Answer similarity (V2)", summary["v2_similarity"], "≥ 0.75", t["similarity"]),
        row("Root-cause match (V2)", summary["v2_root_cause"], "≥ 0.70", t["root_cause"]),
        row("Evidence coverage (V2)", summary["v2_coverage"], "≥ 0.80", t["coverage"]),
        row("Learning improvement", summary["avg_improvement"], "≥ 0.20", t["improvement"]),
        row("Max response time", summary["max_response_s"], "< 15s", t["response_time"]),
        row(
            "Scenario coverage",
            summary["scenario_coverage"],
            "= 1.0",
            t["scenario_coverage"],
        ),
        "",
        "## Per scenario (composite V1 → V2)",
        "| ID | V1 | V2 | improvement |",
        "|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['id']} | {r['v1']['composite']} | {r['v2']['composite']} "
            f"| {r['improvement'] * 100:+.0f}% |"
        )
    return "\n".join(lines) + "\n"


async def run_eval(
    *,
    limit: int | None = None,
    scenario_id: str | None = None,
    delay: float = 0.0,
    fresh: bool = False,
) -> dict[str, Any]:
    """Execute the eval and return the aggregate summary."""
    scenarios = load_scenarios()
    if scenario_id:
        scenarios = [s for s in scenarios if s.id == scenario_id]
    if limit:
        scenarios = scenarios[:limit]
    total = len(scenarios)

    results: list[dict[str, Any]] = []
    async with SessionLocal() as session:
        if fresh:
            await session.execute(delete(LearningEvent))
            await session.commit()
        for i, scenario in enumerate(scenarios):
            try:
                result = await _run_scenario(session, scenario)
                results.append(result)
                log.info("scenario_done", id=scenario.id, improvement=result["improvement"])
            except Exception as exc:  # noqa: BLE001 — record + continue on any scenario failure
                log.warning("scenario_failed", id=scenario.id, error=str(exc))
            if delay and i < len(scenarios) - 1:
                await asyncio.sleep(delay)

        summary = _aggregate(results, total)
        session.add(EvalRun(summary=summary, results=results))
        await session.commit()

    _write_reports(summary, results)
    return summary


def _write_reports(summary: dict[str, Any], results: list[dict[str, Any]]) -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "latest.json").write_text(
        json.dumps({"summary": summary, "results": results}, indent=2), encoding="utf-8"
    )
    (REPORT_DIR / "latest.md").write_text(_render_markdown(summary, results), encoding="utf-8")
