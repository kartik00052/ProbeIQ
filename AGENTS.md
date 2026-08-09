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
- Verification (all from `backend/`, currently clean): `uv run pytest` → 180 passed, 3 skipped; `uv run ruff check app tests`; `uv run mypy app tests`.
- `tests/conftest.py` forces `PROBEIQ_LLM_ENABLED=false`; the 3 skipped tests are live-LLM and only run with `PROBEIQ_LIVE_LLM_TEST=true`.
- Config: pydantic-settings with `PROBEIQ_` prefix (`backend/app/core/config.py`). Copy `backend/.env.example` → `backend/.env` to enable the optional NVIDIA GLM path. Never read or commit `backend/.env` (git-ignored, may hold an API key).
- The interview engine is implemented: LangGraph graph (`app/orchestration/graph.py`) + heuristic question generator/evaluator runs fully offline by default; `app/llm/factory.py` adds optional LLM phrasing/eval (providers `openai` / `openai-compatible` / `nvidia`).
- Accounts: register/login/logout/me with Argon2id hashing and HTTP-only session cookies, persisted in SQLite via SQLAlchemy (`app/core/database.py`, `app/models/`, `app/core/security.py`, `app/services/auth_service.py`, `app/api/routes/auth.py`). Do not invent further DB/Redis models.
- Interview sessions: `InMemorySessionStore` is process-local — a server restart drops all interview sessions (auth accounts/sessions survive in SQLite). Do not invent Redis or other persistence for interview sessions without an explicit request.
- Docker: `docker build -t probeiq-backend ./backend`; from repo root `docker compose up -d` (port 8000) / `docker compose down` (never `down -v`). No postgres service, intentionally.
- API: `POST /api/interview`, keyed by `sessionId`, **requires an authenticated session cookie** (401 `not_authenticated`); a started session is bound to its owner (403 `forbidden` on cross-account access). Auth: `POST /api/auth/register` (201) / `/login` / `/logout`, `GET /api/auth/me` (always 200, `{user: null}` when logged out). Start = `{sessionId, candidate}`, turn = `{sessionId, message}`; response `{reply, done, feedback?}` (feedback present when done). Errors are `{error, detail}` with 400/401/403/404/409/422/500. Do not invent endpoints.
- CORS: configured via `PROBEIQ_CORS_ALLOWED_ORIGINS` (dev default `http://localhost:5173`); credentials are enabled (session cookie), so never use a wildcard; an empty value disables the middleware.

## Frontend (verified working)
- Run from `frontend/`: `npm run dev` (Vite proxy forwards `/api` → `http://localhost:8000`), `npm run build`, `npm run lint`. Playwright e2e in `frontend/e2e/` (`npm run test:e2e`) starts its own backend on :8001 + Vite on :5174; currently 51 passed, 4 skipped.
- Integrate only against the contract above; backend is the source of truth. Don't fabricate endpoints, responses, or interview states.
- Follow `.opencode/FRONTEND.md` conventions: thin pages, zustand stores, centralized framer-motion variants (`src/lib/motion.ts`), `prefers-reduced-motion`, accessible semantics.

## Deployment (live, 2026-08-09)
- **Live URLs:** backend `https://probeiq.onrender.com` (Render, Docker), frontend `https://probe-iq-dun.vercel.app` (Vercel, static SPA). Verified end-to-end: Vercel `/api/*` rewrite → Render, register → 201, `GET /api/auth/me` → `{user}` via cookie round-trip.
- **Render builds the repo-root `Dockerfile`** (copies `backend/...` paths; build context defaults to repo root — do not set root-directory or build-context fields). It installs deps with `uv export --no-group dev --locked` → `pip install -r` into the system Python (not a venv). The image CMD points at `/usr/local/bin/uvicorn`.
- **Render Docker Command must be exactly** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Do NOT prefix it with `/bin/sh -c "..."` — Render already wraps the field in a shell; a nested `sh -c` collapses the whole command into one token and the service exits 127 (`not found`). This bit us on the first deploy.
- **Render env vars:** `PROBEIQ_ENVIRONMENT=production` (enables `Secure` cookie), `PROBEIQ_CORS_ALLOWED_ORIGINS=https://probe-iq-dun.vercel.app`, `PROBEIQ_LLM_ENABLED=false`, `PROBEIQ_DATABASE_URL` empty (SQLite). `backend/Dockerfile` (used by local `docker build ./backend` / compose) is intentionally separate and unchanged.
- **Vercel:** Root Directory = `frontend`; build `npm run build`, output `dist`. `frontend/vercel.json` rewrites `/api/(.*)` → `https://probeiq.onrender.com/api/$1` and falls back other routes to `/index.html` (SPA deep links).
- **Operational constraints:** interview sessions are in-memory (redeploy drops them); SQLite on Render's ephemeral disk resets accounts on redeploy/restart; free Render instances sleep after idle (~30–60 s cold start). Full guide: `deployment.md` (read it before changing anything deployment-related).

## Git
- Follow `.opencode/GIT.md` strictly: no force-push, no `reset --hard`/clean/restore, no history rewrites, no blind `git add .`; targeted staging only.
- `frontend/node_modules/` is untracked (removed from tracking; kept local via `.gitignore`).
- `main` tracks `origin/main`; commit only when explicitly asked, and show exactly what will be staged first.
