# BACKEND.md — Backend engineering rules for ProbeIQ

## Verified stack (as of this document)
- Python >= 3.13 (`backend/pyproject.toml`).
- FastAPI application entrypoint: `backend/app/main.py` (app factory + exception
  handlers), router mounted at `backend/app/api/routes/interview.py`.
- Pydantic v2 schemas (`backend/app/schemas/`) and pydantic-settings config
  (`backend/app/core/config.py`, `PROBEIQ_` env prefix).
- JSON-backed repositories (`backend/app/repositories/`) reading
  `backend/app/data/curriculum.json` and `candidates.json`.
- Deterministic services (`backend/app/services/`): candidate analysis and
  curriculum-day selection.
- Tooling: pytest (42 tests passing), ruff, mypy.
- Declared but **not yet used** in code: langchain, langchain-openai, langgraph,
  asyncpg, redis, sqlalchemy, httpx, uvicorn, python-dotenv. Do not claim these
  are part of the running system.

## Architecture
- Routes → services → repositories. Keep business logic out of route handlers.
- `app/api/routes/` — HTTP endpoints and request/response shaping.
- `app/services/` — business logic (analysis, selection; later interview engine).
- `app/repositories/` — data access (currently JSON files).
- `app/schemas/` — Pydantic models for data and API contracts.
- `app/core/` — config, exceptions (`ProbeIQError` hierarchy), logging
  (`logging.py` is an empty placeholder).
- `app/orchestration/`, `app/agents/`, `app/prompts/` — empty placeholders for
  the planned LangGraph interview engine. Do not treat them as implemented.

## API rules
- Do not invent API endpoints. The contract is defined in
  `.opencode/technical-spec.md`: `POST /api/interview` with `sessionId` plus
  exactly one of `candidate` (start) or `message` (turn), returning
  `{ reply, done, feedback? }`.
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
- Repositories abstract data sources; the current implementation loads JSON
  files and raises typed `DataLoadError`s on failure.
- Do not invent database models.

## Agent/orchestration rules (when implemented later)
- Orchestration (LangGraph) nodes should be small and testable.
- Prompts live in `app/prompts/`; agents in `app/agents/`.

## Error handling
- Raise `ProbeIQError` subclasses for domain errors.
- Let the global handlers convert errors to JSON without leaking stack traces.
- Never log credentials.

## Configuration & environment variables
- All config comes from pydantic-settings with the `PROBEIQ_` prefix
  (`backend/app/core/config.py`).
- Never hardcode secrets.
- Never commit `.env` files.
- Use `.env.example` for documented environment variables. Existing example:
  `PROBEIQ_DATA_DIR`, `PROBEIQ_ENVIRONMENT`.

## Async programming
- The current endpoints are synchronous; the declared async/db/redis stack is
  not yet wired. Do not claim async infrastructure exists.

## Database / Redis
- Declared in `pyproject.toml` but not used. Do not add database models or
  infrastructure the project does not require.

## Testing
- Run `pytest` from `backend/` (test suite: `backend/tests/`).
- Run `ruff check .` and `mypy app tests` from `backend/`.
- Add tests alongside new functionality.
- Never claim tests passed unless they were actually executed.

## Security
- Treat all input as untrusted; validate with schemas.
- Return only appropriate error messages to clients.
- Verify integrations before claiming they work.
