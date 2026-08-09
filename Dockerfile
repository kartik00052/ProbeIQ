# syntax=docker/dockerfile:1
# Render entry point. Lives at the repo root so Render builds it with the
# default repo-root build context (no Docker Build Context setting needed).
# Local `docker build ./backend` / `docker compose` keep using backend/Dockerfile.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install uv, pinned to match the local development toolchain.
RUN pip install --no-cache-dir uv==0.11.21

# Install dependencies first so the layer is cached until the lock changes.
COPY backend/pyproject.toml backend/uv.lock backend/.python-version ./
RUN uv sync --no-group dev --no-install-project --locked

# Copy application source.
COPY backend/app ./app

EXPOSE 8000

# Actual entry point (backend/app/main.py): app = create_app()
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
