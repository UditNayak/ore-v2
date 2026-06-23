"""Programmatic Alembic upgrade, invoked from the app lifespan (and runnable as a CLI)."""

from pathlib import Path

from alembic import command
from alembic.config import Config


def run_migrations() -> None:
    """Upgrade the database to the latest revision (idempotent)."""
    ini_path = Path(__file__).resolve().parents[2] / "alembic.ini"
    command.upgrade(Config(str(ini_path)), "head")


if __name__ == "__main__":
    run_migrations()
