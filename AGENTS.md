# AGENTS.md — ProbeIQ

ProbeIQ is an AI technical-interview agent: a FastAPI backend (`backend/`) that runs an adaptive interview over a 31-day AI-cohort curriculum, plus a React frontend (`frontend/`) that is scaffolded but not yet implemented.

## Instruction sources (read before working)
- `.opencode/*.md` is the canonical project instruction set — follow it: `PROJECT.md`, `AGENT.md`, `FRONTEND.md`, `BACKEND.md`, `GIT.md`, `RULES.md`.
- `.opencode/technical-spec.md` — the single API contract (`POST /api/interview`).
- Root `explanation.md` and `backend/AUDIT_REPORT.md` — most current backend state.
- ⚠️ `.opencode/PROJECT.md` and `.opencode/BACKEND.md` are stale: they claim the interview engine and LLM stack are unimplemented and the suite is "42 tests". The engine is implemented and the suite is 172 tests. `FRONTEND.md` (src empty) is still accurate.
- For frontend design work, use the vendored `impeccable` and `ui-ux-pro-max` skills (in `.opencode/skills/`; also exposed as skills in this session).

## Repo layout
- `backend/` — FastAPI, uv-managed, Python 3.13 (`uv.lock`, `.python-version`). Real entry: `backend/app/main.py` (`app.main:app`). `backend/main.py` is a dead stub.
- `frontend/` — TWO trees, and neither is a runnable ProbeIQ app yet:
  - `frontend/src/` — intended app tree: 53 tracked files, ALL 0-byte placeholders, with the planned architecture (`pages/ components/ hooks/ api/ services/ stores/ types/ constants/ router/ lib/ utils/`).
  - `frontend/frontend/` — nested Vite 8 + React 19 + TS scaffold (the only runnable toolchain: `index.html`, `vite.config.ts`, eslint, tsconfigs, `dev/build/lint/preview` scripts), still the default template with only `react`/`react-dom` deps.
  - `frontend/package.json` (outer) declares the real app deps (axios, framer-motion, react-router-dom, zod, zustand) but has NO scripts, `index.html`, or Vite/TS toolchain.
  - ⚠️ Before building the frontend, confirm with the user which tree is authoritative and where the toolchain should live — this is not settled.

## Backend (verified working)
- Work from `backend/`: `uv sync --locked`, then `uv run uvicorn app.main:app --reload`.
- Verification (all from `backend/`, currently clean): `uv run pytest` → 172 passed, 3 skipped; `uv run ruff check app tests`; `uv run mypy app tests`.
- `tests/conftest.py` forces `PROBEIQ_LLM_ENABLED=false`; the 3 skipped tests are live-LLM and only run with `PROBEIQ_LIVE_LLM_TEST=true`.
- Config: pydantic-settings with `PROBEIQ_` prefix (`backend/app/core/config.py`). Copy `backend/.env.example` → `backend/.env` to enable the optional NVIDIA GLM path. Never read or commit `backend/.env` (git-ignored, may hold an API key).
- No database. `InMemorySessionStore` is process-local — a server restart drops all sessions. Do not invent DB/Redis models.
- Docker: `docker build -t probeiq-backend ./backend`; from repo root `docker compose up -d` (port 8000) / `docker compose down` (never `down -v`). No postgres service, intentionally.
- API: exactly one endpoint `POST /api/interview`, keyed by `sessionId`. Start = `{sessionId, candidate}`, turn = `{sessionId, message}`; response `{reply, done, feedback?}` (feedback present when done). Errors are `{error, detail}` with 404/409/422/500. Do not invent endpoints.
- ⚠️ No CORS middleware (open audit finding P1-3) — a browser frontend on another origin will be blocked until CORS is added.

## Frontend
- No runnable ProbeIQ code exists and `frontend/src/` has no build/lint/test — never claim the frontend builds or runs.
- Integrate only against the contract above; backend is the source of truth. Don't fabricate endpoints, responses, or interview states.
- Follow `.opencode/FRONTEND.md` conventions: thin pages, zustand stores, centralized framer-motion variants (`src/lib/motion.ts`), `prefers-reduced-motion`, accessible semantics.

## Git
- Follow `.opencode/GIT.md` strictly: no force-push, no `reset --hard`/clean/restore, no history rewrites, no blind `git add .`; targeted staging only.
- ⚠️ `frontend/node_modules/` (~6807 files) is tracked despite `.gitignore`. Do not clean it up autonomously — propose it to the user.
- `main` tracks `origin/main`, currently clean (only untracked: `.agents/`, `.claude/`, `.codex/`, `.opencode/skills/impeccable/`, `skills-lock.json`).
- Commit only when explicitly asked; show exactly what will be staged first.
