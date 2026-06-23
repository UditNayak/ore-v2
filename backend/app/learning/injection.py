"""Format learning events for injection into agent prompts (retrieved-memory injection)."""

from app.db.models import LearningEvent

LEARNING_PREAMBLE = (
    "Lessons learned from past expert feedback (apply them if relevant to this question):"
)


def format_learning_event(event: LearningEvent) -> str:
    """Render a single learning event as a compact, actionable lesson."""
    parts = [f"- Lesson: {event.summary}"]
    if event.corrected_root_cause:
        parts.append(f"  Correct root cause: {event.corrected_root_cause}")
    if event.missed_reasoning:
        parts.append(f"  Don't miss: {event.missed_reasoning}")
    if event.missed_sources:
        parts.append(f"  Check sources: {', '.join(event.missed_sources)}")
    return "\n".join(parts)


def learning_block(lessons: list[str]) -> str:
    """Build the prompt block injected into Planner/Reasoner, or '' if there are no lessons."""
    if not lessons:
        return ""
    return f"\n\n{LEARNING_PREAMBLE}\n" + "\n".join(lessons)
