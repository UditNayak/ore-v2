"""Shared keyword-matching helpers for the lexical tools (issue/slack/commit).

Kept in one place (DRY) so all keyword tools tokenize and score consistently.
"""

import re

from sqlalchemy import ColumnElement, or_
from sqlalchemy.orm import InstrumentedAttribute

_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]+")
_STOPWORDS = {
    "the", "a", "an", "is", "was", "were", "are", "of", "to", "for", "and", "or",
    "why", "what", "who", "when", "where", "how", "did", "do", "does", "in", "on",
    "our", "we", "it", "this", "that", "by", "with",
}  # fmt: skip


def terms(query: str, *, min_len: int = 2) -> list[str]:
    """Tokenize a query into meaningful lowercase terms (stopwords removed)."""
    found = [t.lower() for t in _TOKEN.findall(query)]
    return [t for t in found if len(t) >= min_len and t not in _STOPWORDS]


def ilike_any(query_terms: list[str], *columns: InstrumentedAttribute[str]) -> ColumnElement[bool]:
    """OR of case-insensitive LIKE conditions across every (term, column) pair."""
    return or_(*[col.ilike(f"%{t}%") for t in query_terms for col in columns])


def keyword_score(text: str, query_terms: list[str]) -> float:
    """Fraction of query terms present in the text — a simple 0..1 relevance heuristic."""
    if not query_terms:
        return 0.0
    haystack = text.lower()
    hits = sum(1 for t in query_terms if t in haystack)
    return round(hits / len(query_terms), 3)
