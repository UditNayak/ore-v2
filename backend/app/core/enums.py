"""Controlled vocabularies, defined once (DRY) and stored as their string values.

Used across DB models, tool outputs, and agent state so there is a single source of
truth for these categories. See docs/DB_SCHEMA.md.
"""

from enum import StrEnum


class SourceType(StrEnum):
    """Where a piece of evidence came from."""

    DOC = "doc"
    ISSUE = "issue"
    SLACK = "slack"
    COMMIT = "commit"
    LEARNING = "learning"


class DocType(StrEnum):
    """Kind of document in the corpus."""

    WIKI = "wiki"
    POSTMORTEM = "postmortem"
    DESIGN = "design"


class QuestionType(StrEnum):
    """Question category assigned by the Planner."""

    INCIDENT = "incident"
    OWNERSHIP = "ownership"
    RELEASE_DELAY = "release_delay"
    DESIGN_RATIONALE = "design_rationale"
    BLOCKER = "blocker"
    OTHER = "other"


class QuestionStatus(StrEnum):
    """Lifecycle of a question through the reasoning + learning loop."""

    NEW = "new"
    ANSWERED_V1 = "answered_v1"
    AWAITING_HUMAN = "awaiting_human"
    LEARNED = "learned"
    ANSWERED_V2 = "answered_v2"


class IssueStatus(StrEnum):
    """Issue-tracker ticket status."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
