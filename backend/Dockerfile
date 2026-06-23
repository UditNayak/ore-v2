# syntax=docker/dockerfile:1
FROM python:3.12-slim

# uv: fast, reproducible Python package management.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Install dependencies first (better layer caching), then the app source.
COPY pyproject.toml ./
COPY app ./app
RUN uv pip install --system ".[dev]"

EXPOSE 8000

# Compose overrides this with --reload in development.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
