"""The uniform evidence object returned by every tool.

A single shape lets the Investigator and Reasoner treat all sources identically and lets
answers cite sources consistently. See docs/RETRIEVAL.md.
"""

from typing import Any

from pydantic import BaseModel, Field

from app.core.enums import SourceType


class Evidence(BaseModel):
    """One piece of retrieved evidence, from any source."""

    source_type: SourceType
    source_ref: str  # id / key / sha identifying the source row
    title: str | None = None
    snippet: str
    score: float | None = None  # cosine similarity (vector) or keyword heuristic
    metadata: dict[str, Any] = Field(default_factory=dict)
