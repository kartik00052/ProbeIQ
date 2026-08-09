# AGENTS.md — ProbeIQ

ProbeIQ is an AI technical-interview agent: a FastAPI backend (`backend/`) that runs an adaptive interview over a 31-day AI-cohort curriculum, plus a React frontend (`frontend/`) that is implemented and runnable.

## Instruction sources (read before working)
- `.opencode/*.md` is the canonical project instruction set — follow it: `PROJECT.md`, `AGENT.md`, `FRONTEND.md`, `BACKEND.md`, `GIT.md`, `RULES.md`.
- `.opencode/technical-spec.md` — the single API contract (`POST /api/interview`).
- Root `README.md`, `explanation.md`, `frontend/DESIGN.md`, and `backend/AUDIT_REPORT.md` — current state.
- For frontend design work, use the vendored `impeccable` and `ui-ux-pro-max` skills (in `.opencode/skills/`; also exposed as skills in this session).

## Repo layout
- `backend/` — FastAPI, uv-managed, Python 3.13 (`uv.lock`, `.python-version`). Real entry: `backend/app/main.py` (`app.main:app`). `backend/main.py` is a dead stub.
- `frontend/` — ONE runnable package. The toolchain lives at the `frontend/` root (`index.html`, `vite.config.ts`, tsconfigs, `eslint.config.js`, `playwright.config.ts`, `dev/build/lint/preview/test:e2e` scripts) and the application source in `frontend/src/` (`pages/ components/ hooks/ api/ services/ stores/ types/ constants/ router/ lib/ utils/ layouts/`). The obsolete nested `frontend/frontend/` scaffold was removed.

## Backend (verified working)
- Work from `backend/`: `uv sync --locked`, then `uv run uvicorn app.main:app --reload`.
- Verification (all from `backend/`, currently clean): `uv run pytest` → 174 passed, 3 skipped; `uv run ruff check app tests`; `uv run mypy app tests`.
- `tests/conftest.py` forces `PROBEIQ_LLM_ENABLED=false`; the 3 skipped tests are live-LLM and only run with `PROBEIQ_LIVE_LLM_TEST=true`.
- Config: pydantic-settings with `PROBEIQ_` prefix (`backend/app/core/config.py`). Copy `backend/.env.example` → `backend/.env` to enable the optional NVIDIA GLM path. Never read or commit `backend/.env` (git-ignored, may hold an API key).
- The interview engine is implemented: LangGraph graph (`app/orchestration/graph.py`) + heuristic question generator/evaluator runs fully offline by default; `app/llm/factory.py` adds optional LLM phrasing/eval (providers `openai` / `openai-compatible` / `nvidia`).
- No database. `InMemorySessionStore` is process-local — a server restart drops all sessions. Do not invent DB/Redis models.
- Docker: `docker build -t probeiq-backend ./backend`; from repo root `docker compose up -d` (port 8000) / `docker compose down` (never `down -v`). No postgres service, intentionally.
- API: exactly one endpoint `POST /api/interview`, keyed by `sessionId`. Start = `{sessionId, candidate}`, turn = `{sessionId, message}`; response `{reply, done, feedback?}` (feedback present when done). Errors are `{error, detail}` with 400/404/409/422/500. Do not invent endpoints.
- CORS: configured via `PROBEIQ_CORS_ALLOWED_ORIGINS` (dev default `http://localhost:5173`); an empty value disables the middleware.

## Frontend (verified working)
- Run from `frontend/`: `npm run dev` (Vite proxy forwards `/api` → `http://localhost:8000`), `npm run build`, `npm run lint`. Playwright e2e in `frontend/e2e/` (`npm run test:e2e`) starts its own backend on :8001 + Vite on :5174; 22 tests currently pass.
- Integrate only against the contract above; backend is the source of truth. Don't fabricate endpoints, responses, or interview states.
- Follow `.opencode/FRONTEND.md` conventions: thin pages, zustand stores, centralized framer-motion variants (`src/lib/motion.ts`), `prefers-reduced-motion`, accessible semantics.

## Git
- Follow `.opencode/GIT.md` strictly: no force-push, no `reset --hard`/clean/restore, no history rewrites, no blind `git add .`; targeted staging only.
- `frontend/node_modules/` is untracked (removed from tracking; kept local via `.gitignore`).
- `main` tracks `origin/main`; commit only when explicitly asked, and show exactly what will be staged first.
