# ProbeIQ — AI Interview Agent

## Project purpose
ProbeIQ is an AI-powered technical interview agent. It interviews a candidate
about an AI-engineering curriculum they have completed, based on the candidate's
submitted learning data, and produces structured feedback.

The submission contract is defined in `technical-spec.md`: a single
unauthenticated `POST /api/interview` endpoint, keyed by `sessionId`.

## High-level architecture
- **Backend** (`backend/`): FastAPI service receiving the interview requests.
  Implements the data foundation (schemas, repositories, deterministic
  analysis/selection services) and a placeholder `/api/interview` route.
- **Frontend** (`frontend/`): client application. Currently an empty source
  scaffold (no runnable code).
- **AI/agent layer**: planned (LangGraph orchestration, agents, prompts). Not yet
  implemented; only empty placeholder modules exist.

## Repository structure
- `.opencode/` — instructions for AI agents (`PROJECT.md`, `AGENT.md`, `GIT.md`,
  `FRONTEND.md`, `BACKEND.md`, `RULES.md`), the `technical-spec.md` API contract,
  sample data (`candidates.json`, `curriculum.json`), and the `ui-ux-pro-max`
  UI/UX skill.
- `backend/` — FastAPI application (see `BACKEND.md`).
- `frontend/` — client application scaffold (see `FRONTEND.md`).

## Frontend responsibility
Render the interview experience: candidate setup, conversation, and final
feedback screens. See `FRONTEND.md`. **Not implemented yet** — the `src/` tree
currently contains empty files only.

## Backend responsibility
Expose `POST /api/interview`, validate the request contract, maintain interview
state per `sessionId`, run the interview (question generation, evaluation,
feedback), and return responses. See `BACKEND.md`. Only the foundation is
implemented so far.

## AI/agent responsibility (planned)
- Analyze candidate learning evidence.
- Select relevant curriculum topics for questioning.
- Generate questions, evaluate answers, generate feedback.

No agent code is implemented. The deterministic evidence/selection services in
`backend/app/services/` are the only implemented analysis logic.

## Data flow (verified)
`backend/app/data/candidates.json` + `curriculum.json`
→ repositories (`app/repositories/`) validate and load
→ services (`app/services/`) compute deterministic candidate analysis and
  curriculum-day selection
→ `/api/interview` route returns a placeholder dev response (no real interview
  yet).

## Technology stack (verified)
Backend:
- Python >= 3.13 (declared in `backend/pyproject.toml`).
- FastAPI, Pydantic v2, pydantic-settings (used by implemented code).
- pytest, ruff, mypy (configured; currently passing).
- Declared but **not yet used**: langchain, langgraph, langchain-openai,
  asyncpg, redis, sqlalchemy, httpx, uvicorn, python-dotenv.

Frontend:
- Declared dependencies in `frontend/package.json`: axios, framer-motion,
  react-router-dom, zod, zustand; eslint toolchain under `devDependencies`.
- React, TypeScript, and Vite are **not currently declared** in `package.json`;
  the scaffold uses `.tsx`/`.ts` files, but their stack is not verified at the
  dependency level.

## Current implementation status
Implemented:
- Backend data schemas, JSON repositories, deterministic candidate analysis and
  curriculum-day selection services, config, typed exceptions, error handlers.
- `POST /api/interview` endpoint that validates the contract and returns a
  clearly-marked dev placeholder reply.
- Test suite (42 tests) covering schemas, repositories, services, and the API.
  Verified passing via pytest; ruff and mypy clean.

Planned / not yet implemented:
- Real interview engine (question generation, evaluation, feedback).
- LangGraph orchestration graph and nodes (`app/orchestration/`), agents
  (`app/agents/`), prompts (`app/prompts/`), session state persistence.
- Database / Redis integration (declared but unused).
- All frontend application code (empty scaffold).

## Known limitations
- The interview route returns a placeholder reply; sessions do not yet maintain
  real state or produce questions/feedback.
- Frontend has no runnable code.
- `frontend/node_modules/` is tracked in Git (~6807 files) despite `.gitignore`;
  this inflates the repository (cleanup pending — see `GIT.md`).

## Not currently verified
- End-to-end frontend ↔ backend communication.
- Any real LLM/agent behavior.
- A Vite/React/TypeScript frontend build configuration.
