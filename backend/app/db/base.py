"""Declarative base and shared column helpers for all ORM models."""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def created_at_column() -> Mapped[datetime]:
    """A UTC `timestamptz` default-now creation timestamp (DRY across models)."""
    return mapped_column(server_default=func.now())
