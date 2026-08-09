# ProbeIQ — AI Interview Agent

## Project purpose
ProbeIQ is an AI-powered technical interview agent. It interviews a candidate
about an AI-engineering curriculum they have completed, based on the candidate's
submitted learning data, and produces structured feedback.

The submission contract is defined in `technical-spec.md`: a `POST /api/interview`
endpoint, keyed by `sessionId`. As a deliberate, user-approved extension the
running system additionally guards the endpoint with account authentication
(`/api/auth/register`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`)
using HTTP-only session cookies; see `technical-spec.md` §Auth extension.

## High-level architecture
- **Backend** (`backend/`): FastAPI service running the real adaptive interview
  engine. A deterministic LangGraph orchestration core drives candidate
  analysis, topic planning, question generation, evaluation, and feedback; an
  optional LLM layer only rephrases questions and grades answers (see
  `BACKEND.md`).
- **Frontend** (`frontend/`): runnable Vite + React app. Single package — the
  toolchain lives at the `frontend/` root and the application source in
  `frontend/src/` (see `FRONTEND.md`).

## Repository structure
- `.opencode/` — instructions for AI agents (`PROJECT.md`, `AGENT.md`, `GIT.md`,
  `FRONTEND.md`, `BACKEND.md`, `RULES.md`), the `technical-spec.md` API contract,
  sample data (`candidates.json`, `curriculum.json`), and vendored skills
  (`skills/impeccable`, `skills/ui-ux-pro-max`).
- `backend/` — FastAPI application (see `BACKEND.md`).
- `frontend/` — client application (see `FRONTEND.md`).

## Frontend responsibility
Render the interview experience: candidate setup, conversation, and final
feedback screens. Implemented in `frontend/src/` (pages, components, hooks, api,
services, stores, types, constants, router, lib, utils, layouts). Verified with
`npm run build`, `npm run lint`, and a Playwright e2e suite in `frontend/e2e/`.
See `FRONTEND.md`.

## Backend responsibility
Expose the auth endpoints and `POST /api/interview`, validate the request
contract, maintain interview state per `sessionId` bound to the authenticated
user, run the interview (candidate analysis, topic planning, question
generation, answer evaluation, feedback), and return responses. See
`BACKEND.md`. The engine is implemented and test-covered.

## Interview engine (implemented)
- LangGraph orchestration graph (`backend/app/orchestration/graph.py`) driving
  nodes: analyze candidate, plan interview, generate question, decide next step,
  evaluate response, generate feedback.
- Deterministic services compute candidate analysis and curriculum-day/topic
  selection; question generation and evaluation fall back to templates and
  heuristics so the engine runs fully offline by default.
- Optional LLM layer (`backend/app/llm/factory.py`) rephrases questions and
  grades answers. Providers: `openai-compatible` (default), `openai`, `nvidia`
  (NVIDIA-hosted GLM). The LLM is enabled only via `PROBEIQ_LLM_*` config and is
  never required for a working interview.

## Data flow (verified)
`backend/app/data/candidates.json` + `curriculum.json`
→ repositories (`app/repositories/`) validate and load
→ services (`app/services/`) compute deterministic candidate analysis,
  curriculum-day selection, and topic planning
→ LangGraph interview graph runs the adaptive interview (deterministic when the
  LLM is disabled)
→ `app/repositories/session_store.py` persists per-`sessionId` state in memory
→ `/api/interview` returns `{ reply, done, feedback? }`.

## Technology stack (verified)
Backend:
- Python >= 3.13 (declared in `backend/pyproject.toml`), FastAPI, Pydantic v2,
  pydantic-settings (`PROBEIQ_` env prefix), SQLAlchemy 2.x + SQLite (auth
  persistence), argon2-cffi (Argon2id), email-validator, langgraph,
  langchain-openai / langchain-nvidia-ai-endpoints (LLM providers), uvicorn.
- Tooling: pytest (180 passed, 3 skipped), ruff, mypy — all clean.
- Declared but **not used** by app code: asyncpg, redis, httpx,
  python-dotenv. Do not treat them as part of the running system.

Frontend:
- Single package at `frontend/`: React 19, TypeScript, Vite 8, Tailwind v4,
  framer-motion, zustand, axios, react-router-dom, zod, three +
  @react-three/fiber + @react-three/drei (lazy-loaded WebGL presence).
- Toolchain (scripts `dev`/`build`/`lint`/`preview`/`test:e2e`,
  `vite.config.ts`, `index.html`, tsconfigs, eslint) lives at the `frontend/`
  root. Verified: `npm run build` and `npm run lint` pass.

## Current implementation status
Implemented:
- Backend: interview engine (LangGraph orchestration, agents, prompts, LLM
  factory), JSON repositories, in-memory session store, deterministic
  analysis/selection/planning services, config, typed exceptions, error
  handlers, environment-configured CORS.
- Authentication: register/login/logout/me with Argon2id password hashing,
  opaque tokens in HTTP-only session cookies, SQLite persistence via
  SQLAlchemy (`app/models/`, `app/core/database.py`, `app/core/security.py`,
  `app/services/auth_service.py`, `app/api/routes/auth.py`).
- `POST /api/interview` requiring an authenticated session and returning
  `{ reply, done, feedback? }`; started sessions are bound to the owning user
  (cross-account access is rejected with 403).
- Test suite (180 tests) covering schemas, repositories, services, orchestration,
  auth, and the API; 3 skipped tests are live-LLM only.
- Frontend: runnable app (landing, login, register, candidate setup, interview,
  feedback pages), auth + interview zustand stores, API client/services, route
  guards, WebGL presence with fallbacks, reduced motion. Verified build/lint
  and a Playwright e2e suite (51 passed, 4 skipped).

Planned / not yet implemented:
- Persisted interview sessions (accounts persist in SQLite, but interview
  sessions are in-memory and lost on server restart).
- Auth hardening: rate limiting / brute-force protection on login.

## Known limitations
- Interview session state is process-local (`InMemorySessionStore`): a server
  restart drops all interview sessions (auth accounts/sessions persist in
  SQLite).
- No rate limiting / lockout on auth endpoints.
- LLM phrasing/eval is optional and not exercised by the default test suite.

## Not currently verified
- Live LLM behavior (the 3 skipped tests require `PROBEIQ_LIVE_LLM_TEST=true`
  and a working provider/key).
