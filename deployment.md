# ProbeIQ — Deployment Guide

Deployment plan for the current verified state of ProbeIQ. Everything in this guide was verified locally against a production-shape replica of this exact architecture (see "Production-shape verification" below).

## Architecture

```
Browser
   │  (same-origin: https://<frontend>.vercel.app)
   ▼
Vercel (static SPA: frontend/dist, built by Vite)
   │  rewrites /api/* → https://<backend>.onrender.com/api/*
   ▼
Render (FastAPI via Docker: backend/)
```

Because the Vercel rewrite is same-origin, the browser talks only to the Vercel origin. The backend's session cookie (`HttpOnly`, `SameSite=Lax`) is set on the Vercel domain and round-trips through the proxy. No CORS is required in production; `PROBEIQ_CORS_ALLOWED_ORIGINS` still matters for direct/cross-origin calls and should be set to the Vercel origin.

## Backend → Render

The backend has no `requirements.txt` (uv-managed), so Render's default Python build will not work. Use the **Docker** runtime, which is already set up (`backend/Dockerfile`).

Service fields (important — the **build context must point at `backend`**, or the Dockerfile's `COPY`s won't resolve and the build fails with "`/pyproject.toml` not found"):

| Field | Value |
|---|---|
| Name / Language / Branch | `ProbeIQ` / `Docker` / `main` |
| Root Directory | *(empty)* |
| Dockerfile Path | `backend/Dockerfile` |
| **Docker Build Context Directory** | **`backend`** |
| Docker Command | `/bin/sh -c "uvicorn app.main:app --host 0.0.0.0 --port $PORT"` |
| Health Check Path | *(empty — the app has no `/healthz`; a 404 there marks the service unhealthy)* |

`/bin/sh -c` is required so Render's `$PORT` env var expands (the image's `CMD` hardcodes port 8000). `app/.venv/bin` is on `PATH`; `uv sync --no-group dev --no-install-project --locked` runs at build time.

Environment variables (`PROBEIQ_` prefix, pydantic-settings — see `backend/.env.example`):
- `PROBEIQ_ENVIRONMENT=production` — required; the session cookie only gets the `Secure` flag in production (`backend/app/api/routes/auth.py`).
- `PROBEIQ_CORS_ALLOWED_ORIGINS` — the deployed frontend origin (e.g. `https://probe-iq.vercel.app`); never `*`.
- `PROBEIQ_LLM_ENABLED=false` — and **delete all other `PROBEIQ_LLM_*` rows**, so startup never parses a bad LLM roster and no keys are uploaded.
- `PROBEIQ_DATABASE_URL` — leave empty (SQLite under `app/data`); do not use Render's Postgres "Generate".

Constraints:
- **Single instance.** Interview sessions live in an in-memory store; a redeploy/restart drops in-progress interviews.
- **SQLite on Render's ephemeral disk.** Accounts reset on each redeploy/restart. Fine for a demo; durable accounts would need a managed Postgres (out of scope unless requested).

## Frontend → Vercel

1. Import the repo; set the **Root Directory** to `frontend` (the Vercel project root). Vercel auto-detects Vite:
   - Build command: `npm run build` (`tsc -b && vite build`, already the `build` script).
   - Output directory: `dist`.
2. `vercel.json` (committed at `frontend/vercel.json`, read from the project root `frontend/`) does two things:
   - `/api/(.*)` → `https://probeiq-backend.onrender.com/api/$1` — same-origin proxy to the backend. **Replace this URL with the real Render service URL** (Render assigns a fixed `<name>.onrender.com` host) before or right after first deploy.
   - `/(.*)` → `/index.html` — SPA fallback so deep links (`/setup`, `/interview`, `/complete`, `/login`, `/register`) resolve on the production build.
   - `rewrites` (not `routes`) is used deliberately: it checks the filesystem first, so static assets are served normally while only unknown routes fall back to `index.html`.
3. No code changes needed: `frontend/src/api/client.ts` already uses `baseURL: '/api'` with `withCredentials: true`, which is exactly right for same-origin proxying.

## Post-deploy verification checklist

Run against the deployed site (not localhost):

- [ ] Deep link loads: `https://<frontend>.vercel.app/setup` renders the app (SPA fallback).
- [ ] Proxy works: register a new account → lands on `/setup`.
- [ ] Cookie round-trip: after login, `GET /api/auth/me` returns `{"user": {...}}` (not `null`). This proves the rewrite forwards `Set-Cookie` and the session cookie back.
- [ ] Full journey: begin an interview, answer through to `/complete`, confirm the report renders.
- [ ] Account isolation: a second user must land on `/setup`, never another user's report.

## Production-shape verification (how this was proven locally)

A local replica of this exact architecture — Vite's `dist/` served statically + a same-origin `/api` proxy to a running backend — passed a real-browser (Playwright) journey:

- register → begin → full interview → complete → report rendered
- logout → landing; unauthenticated deep-link redirect
- account isolation between two users
- session cookie set via the proxied response (`HttpOnly`, `SameSite=Lax`) and honored on subsequent calls
- zero uncaught page errors

The one thing a local replica cannot prove is Vercel/Render platform behavior (free-tier cold starts, CDN edge caching). Render free instances sleep after idle; the first request after a pause can take ~30–60s. Not a correctness issue.

## Optional hardening (not required)

- Vercel caches external-origin rewrites only when the upstream sends caching headers; FastAPI sends none, so `/api` responses are not CDN-cached. If you ever add `Cache-Control` to API responses, add `x-vercel-enable-rewrite-caching: 0` in `vercel.json` for `/api/(.*)` to keep interview state uncached.
- Add a `/healthz` endpoint to the backend if Render health checks are desired (not currently required to boot).
