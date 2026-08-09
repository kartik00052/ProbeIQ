# BACKEND.md — Backend engineering rules for ProbeIQ

## Verified stack (as of this document)
- Python >= 3.13 (`backend/pyproject.toml`).
- FastAPI application entrypoint: `backend/app/main.py` (app factory + exception
  handlers + CORS + `init_db`), routers mounted at `backend/app/api/routes/`
  (`auth.py` and `interview.py`).
- Pydantic v2 schemas (`backend/app/schemas/`) and pydantic-settings config
  (`backend/app/core/config.py`, `PROBEIQ_` env prefix).
- JSON-backed repositories (`backend/app/repositories/`) reading
  `backend/app/data/curriculum.json` and `candidates.json`.
- Auth persistence: SQLAlchemy 2.x + SQLite (default `app/data/probeiq.db`,
  override via `PROBEIQ_DATABASE_URL`). ORM models in `app/models/`
  (`User`, `AuthSession`), engine/session wiring in `app/core/database.py`,
  Argon2id hashing + token generation in `app/core/security.py`, domain logic in
  `app/services/auth_service.py`.
- Deterministic services (`backend/app/services/`): candidate analysis,
  curriculum-day selection, topic planning, and the interview engine service.
- Interview engine: LangGraph graph (`app/orchestration/graph.py`) with nodes
  for analyze / plan / generate / decide / evaluate / feedback, prompt templates
  (`app/prompts/`), and agents (`app/agents/`). Runs offline and deterministically
  by default (heuristic generator/evaluator); the LLM layer is optional.
- LLM factory (`app/llm/factory.py`): `openai` / `openai-compatible` →
  ChatOpenAI, `nvidia` → ChatNVIDIA (NVIDIA-hosted GLM).
- Tooling: pytest (180 passed, 3 skipped — the skips are live-LLM only), ruff,
  mypy.
- Declared but **not used** in code: asyncpg, redis, httpx, python-dotenv. Do
  not claim these are part of the running system.

## Architecture
- Routes → services → repositories. Keep business logic out of route handlers.
- `app/api/routes/` — HTTP endpoints and request/response shaping (`auth.py` for
  register/login/logout/me, `interview.py` for the interview).
- `app/services/` — business logic (analysis, selection, planning, interview,
  auth).
- `app/repositories/` — data access (JSON files), `session_store.py`
  (in-memory per-`sessionId` interview persistence), and SQLAlchemy-backed
  repositories (`user_repository.py`, `auth_session_repository.py`).
- `app/models/` — SQLAlchemy ORM models for auth (`User`, `AuthSession`).
- `app/schemas/` — Pydantic models for data and API contracts.
- `app/core/` — config, exceptions (`ProbeIQError` hierarchy), `security.py`
  (hashing/tokens), `database.py` (engine + sessions), logging
  (`logging.py` is still an empty placeholder).
- `app/orchestration/` — the LangGraph interview graph and nodes; implemented.
- `app/agents/`, `app/prompts/` — LLM-backed agents and prompt templates;
  implemented, but only exercised when the LLM is enabled.
- `app/llm/` — ChatOpenAI / ChatNVIDIA factory; implemented.

## API rules
- Do not invent API endpoints. The contract is defined in
  `.opencode/technical-spec.md`: `POST /api/interview` with `sessionId` plus
  exactly one of `candidate` (start) or `message` (turn), returning
  `{ reply, done, feedback? }`.
- Auth endpoints (the user-approved extension): `POST /api/auth/register`
  (201), `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`.
- `POST /api/interview` requires an authenticated session (401
  `not_authenticated` otherwise); a started session is bound to the
  authenticated user and cross-account access is rejected (403 `forbidden`).
  The gate is `get_current_user` in `app/api/dependencies.py` — never trust
  client-side route guards.
- Validate external input via Pydantic schemas.
- Return appropriate errors using `ProbeIQError` subclasses and the global
  exception handlers in `app/main.py`.

## Pydantic schema rules
- Keep schemas in `app/schemas/`, grouped by domain.
- Use validators for cross-field rules (e.g. `Mission` passed/skipped
  exclusivity).
- Reuse schema types rather than duplicating field definitions.

## Service layer rules
- Services must be deterministic and testable.
- Keep pure logic free of HTTP concerns.
- Preserve the existing architecture unless explicitly asked to change it.

## Repository layer rules
- Repositories abstract data sources; JSON repositories load
  `curriculum.json` / `candidates.json` and raise typed `DataLoadError`s on
  failure; auth repositories use SQLAlchemy sessions from `app/core/database.py`.
- Do not invent database models beyond the existing auth models; interview
  sessions intentionally remain in-memory.

## Agent/orchestration rules
- Orchestration (LangGraph) nodes are small and testable.
- Prompts live in `app/prompts/`; agents in `app/agents/`.
- The deterministic controller decides WHAT to probe; the LLM only decides HOW
  to phrase a question and how to judge an answer. Never make the interview
  require an LLM — the offline heuristic path must always work.

## Error handling
- Raise `ProbeIQError` subclasses for domain errors.
- Let the global handlers convert errors to JSON without leaking stack traces.
- Never log credentials.

## Configuration & environment variables
- All config comes from pydantic-settings with the `PROBEIQ_` prefix
  (`backend/app/core/config.py`).
- Never hardcode secrets.
- Never commit `.env` files.
- Use `.env.example` for documented environment variables. Key variables:
  `PROBEIQ_LLM_ENABLED`, `PROBEIQ_LLM_PROVIDER`, `PROBEIQ_LLM_MODEL`,
  `PROBEIQ_LLM_BASE_URL`, `PROBEIQ_LLM_API_KEY`, `PROBEIQ_LLM_MAX_RETRIES`,
  `PROBEIQ_CORS_ALLOWED_ORIGINS`, `PROBEIQ_DATA_DIR`, `PROBEIQ_ENVIRONMENT`,
  `PROBEIQ_DATABASE_URL`, `PROBEIQ_AUTH_COOKIE_NAME`,
  `PROBEIQ_AUTH_SESSION_TTL_DAYS`.

## Async programming
- The current endpoints are synchronous; the declared async/redis stack is
  not yet wired. Do not claim async infrastructure exists.

## Database
- Auth persistence uses SQLite via SQLAlchemy (sync). `app/core/database.py`
  owns the engine/session factory; tables are created idempotently in `init_db`
  at app startup. Default DB file: `app/data/probeiq.db` (git-ignored).
- `asyncpg` and `redis` are declared in `pyproject.toml` but not used. Do not
  add database models or infrastructure the project does not require.
- Interview sessions stay in `InMemorySessionStore` — do not persist them
  without an explicit request.

## Setup & infrastructure (uv + Docker)
- Dependency management is uv (pinned to 0.11.21; Python 3.13 via
  `backend/.python-version`). From `backend/`:
  - `uv sync --locked` — install the locked environment.
  - `uv run pytest` / `uv run ruff check app tests` / `uv run mypy app tests`.
- Local run: `cd backend && uv run uvicorn app.main:app --reload` (entry point is
  `app.main:app`, defined in `backend/app/main.py`).
- Secrets: copy `backend/.env.example` to `backend/.env` and fill in values such
  as `PROBEIQ_LLM_API_KEY`. `backend/.env` is git-ignored; `.env.example`
  contains placeholders only and must never carry real credentials.
- Docker:
  - Build: `docker build -t probeiq-backend ./backend` (`backend/Dockerfile`,
    python:3.13-slim, production dependency group only).
  - Start: `docker compose up -d` from the repo root (single `backend` service
    on port 8000; `backend/.env` is loaded when present and is optional).
  - Stop: `docker compose down`. Do NOT use `down -v` (it deletes named volumes).
- PostgreSQL: NOT currently used by the application — auth persistence is
  SQLite (a separate Postgres service would add no value). The
  `asyncpg`/`redis` deps declared in `backend/pyproject.toml` are unused
  placeholders; a Postgres migration is a separate follow-up item.

## Deployment (production)
- Live (2026-08-09): backend `https://probeiq.onrender.com` (Render, Docker),
  frontend `https://probe-iq-dun.vercel.app` (Vercel). See `deployment.md`
  for the authoritative guide; read it before changing anything deployment-related.
- Render builds the **repo-root `Dockerfile`** (build context = repo root; do
  not set root-directory/build-context fields). It runs
  `uv export --no-group dev --locked --format requirements.txt` then
  `pip install -r` into the **system Python** (`/usr/local`), not a venv.
  `backend/Dockerfile` is the local-dev file and is intentionally separate.
- **Render Docker Command must be exactly**
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Do NOT prefix it with
  `/bin/sh -c "..."` — Render already wraps the field in a shell; a nested
  `sh -c` collapses the command into one token and the service exits 127.
- Render env vars: `PROBEIQ_ENVIRONMENT=production`,
  `PROBEIQ_CORS_ALLOWED_ORIGINS=https://probe-iq-dun.vercel.app`,
  `PROBEIQ_LLM_ENABLED=false` (delete all other `PROBEIQ_LLM_*` rows),
  `PROBEIQ_DATABASE_URL` empty (SQLite on ephemeral disk).
- Operational constraints: interview sessions are in-memory and SQLite accounts
  reset on redeploy/restart; free Render instances sleep after idle.

## Testing
- Run `pytest` from `backend/` (test suite: `backend/tests/`; 180 passed,
  3 skipped — the skips are live-LLM only).
- Run `ruff check .` and `mypy app tests` from `backend/`.
- Add tests alongside new functionality.
- Never claim tests passed unless they were actually executed.

## Security
- Treat all input as untrusted; validate with schemas.
- Return only appropriate error messages to clients.
- Passwords are hashed with Argon2id (`app/core/security.py`); login errors are
  deliberately generic so the API never reveals whether an email exists.
- Session tokens are opaque, server-side, and revocable; the cookie is
  HTTP-only + `SameSite=Lax` (Secure in production). CORS allows credentials
  only to explicit origins — never add a wildcard.
- Verify integrations before claiming they work.
