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

1. Import the repo; choose **Docker** as the runtime.
2. Root directory: `backend`.
3. **Start command** (overrides the Dockerfile's hardcoded port 8000 so Render's `$PORT` is honored):
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
   (`app/.venv/bin` is on `PATH` inside the image; `uv sync --no-group dev --no-install-project --locked` runs at build time.)
4. Environment variables (see `backend/.env.example` and `backend/app/core/config.py`):
   - `PROBEIQ_CORS_ALLOWED_ORIGINS` — `https://<frontend>.vercel.app` (never `*`; credentials are enabled).
   - `PROBEIQ_LLM_ENABLED` — omit/false for the offline heuristic engine (works out of the box).
   - Optional, only for LLM phrasing/eval: `PROBEIQ_OPENAI_API_KEY`, `PROBEIQ_OPENAI_BASE_URL`, `PROBEIQ_OPENAI_MODEL`, `PROBEIQ_NVIDIA_*` (see `.env.example`).
5. Constraints to remember:
   - **Single instance.** Interview sessions live in an in-memory store; a redeploy/restart drops in-progress interviews.
   - **SQLite on Render's ephemeral disk.** Accounts/sessions reset on each redeploy/restart. Fine for a demo; durable accounts would need a managed Postgres (out of scope unless requested).

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
