# syntax=docker/dockerfile:1
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
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --no-group dev --no-install-project --locked

# Copy application source.
COPY app ./app

EXPOSE 8000

# Actual entry point (backend/app/main.py): app = create_app()
# .venv/bin is on PATH (ENV above); dependencies were synced at build time.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
