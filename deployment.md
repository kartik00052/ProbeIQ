# ProbeIQ — Deployment Guide

## Status: DEPLOYED AND VERIFIED (2026-08-09)

| Service | Platform | URL | Status |
|---|---|---|---|
| Backend | Render (Docker) | `https://probeiq.onrender.com` | Live — `GET /api/auth/me` → `200 {"user":null}` |
| Frontend | Vercel (static SPA) | `https://probe-iq-dun.vercel.app` | Live — `/setup` renders, `/api` proxy reaches backend |

End-to-end verified through the Vercel origin: register → `201`, then `GET /api/auth/me` → `{"user":{"id":...,"email":...}}` (session cookie round-trips through the proxy). See the post-deploy checklist below.

This guide documents how the deployment was built and how to reproduce it. Everything was first verified locally against a production-shape replica (see "Production-shape verification" below).

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

The backend has no `requirements.txt` (uv-managed), so Render's default Python build will not work. Use the **Docker** runtime. The repo has two Dockerfiles:

- `Dockerfile` (repo root) — **the one Render uses.** It copies `backend/...` paths relative to the repo-root build context, so Render needs **no** root-directory or build-context overrides.
- `backend/Dockerfile` — used by local `docker build ./backend` and `docker compose` (build context `backend/`). Do not point Render at it; it would need its build context set to `backend/`, and that dashboard field has proven unreliable.

Service fields:

| Field | Value |
|---|---|
| Name / Language / Branch | `ProbeIQ` / `Docker` / `main` |
| Root Directory | *(empty)* |
| Dockerfile Path | `Dockerfile` |
| Docker Build Context Directory | *(empty — defaults to repo root)* |
| Docker Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | *(empty — the app has no `/healthz`; a 404 there marks the service unhealthy)* |

Do **not** prefix the Docker Command with `/bin/sh -c "..."`. Render already runs the field through `/bin/sh -c`, so a nested `sh -c` with quotes collapses the whole command into one token and the service exits 127 (`not found`). At build time `uv export --no-group dev --locked` produces a hashed requirements file and pip installs it into the system Python (`/usr/local`); `uvicorn` resolves there. The image's `CMD` (hardcoded port 8000) is only a fallback — the Docker Command overrides it with Render's `$PORT`.

Environment variables (`PROBEIQ_` prefix, pydantic-settings — see `backend/.env.example`):
- `PROBEIQ_ENVIRONMENT=production` — required; the session cookie only gets the `Secure` flag in production (`backend/app/api/routes/auth.py`).
- `PROBEIQ_CORS_ALLOWED_ORIGINS` — the deployed frontend origin `https://probe-iq-dun.vercel.app`; never `*`.
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
   - `/api/(.*)` → `https://probeiq.onrender.com/api/$1` — same-origin proxy to the backend (already committed in `frontend/vercel.json`). If the backend moves, update this URL to the new Render `<name>.onrender.com` host.
   - `/(.*)` → `/index.html` — SPA fallback so deep links (`/setup`, `/interview`, `/complete`, `/login`, `/register`) resolve on the production build.
   - `rewrites` (not `routes`) is used deliberately: it checks the filesystem first, so static assets are served normally while only unknown routes fall back to `index.html`.
3. No code changes needed: `frontend/src/api/client.ts` already uses `baseURL: '/api'` with `withCredentials: true`, which is exactly right for same-origin proxying.

## Post-deploy verification checklist

Verified 2026-08-09 against the live site:

- [x] Deep link loads: `https://probe-iq-dun.vercel.app/setup` renders the app (SPA fallback).
- [x] Proxy works: register a new account (via the Vercel origin) → `201`.
- [x] Cookie round-trip: after register/login, `GET /api/auth/me` returns `{"user": {...}}` (not `null`) — proves the rewrite forwards `Set-Cookie` and the session cookie back.
- [ ] Full journey: begin an interview, answer through to `/complete`, confirm the report renders. *(Manual browser check — pending)*
- [ ] Account isolation: a second user must land on `/setup`, never another user's report. *(Manual browser check — pending)*

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
