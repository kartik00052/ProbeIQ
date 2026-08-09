# syntax=docker/dockerfile:1
# Render entry point. Lives at the repo root so Render builds it with the
# default repo-root build context (no Docker Build Context setting needed).
# Local `docker build ./backend` / `docker compose` keep using backend/Dockerfile.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install uv, pinned to match the local development toolchain.
RUN pip install --no-cache-dir uv==0.11.21

# Install dependencies into the system Python (/usr/local) rather than a venv:
# Render's runtime did not expose /app/.venv/bin, so venv console scripts did
# not resolve at startup (exit 127). uv still resolves the locked set; pip
# performs the system-wide install.
COPY backend/pyproject.toml backend/uv.lock backend/.python-version ./
RUN uv export --no-group dev --locked --format requirements.txt --output-file /tmp/requirements.txt \
    && pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application source.
COPY backend/app ./app

EXPOSE 8000

# Actual entry point (backend/app/main.py): app = create_app()
CMD ["/usr/local/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
