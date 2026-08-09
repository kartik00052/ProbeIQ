# ProbeIQ — Backend Explanation & Current State

> **Addendum (2026-08-09, commit `b9a711a` "feat(auth)…").** The snapshot below
> predates authentication. Current state at a glance:
>
> - **New endpoints** (user-approved extension to `technical-spec.md`):
>   `POST /api/auth/register` (201), `POST /api/auth/login`,
>   `POST /api/auth/logout`, `GET /api/auth/me`. `POST /api/interview` now
>   **requires** an authenticated session (401 `not_authenticated`; 403
>   `forbidden` when driving another account's session).
> - **Auth stack:** Argon2id hashing (`app/core/security.py`), opaque
>   `secrets.token_urlsafe(48)` tokens, HTTP-only `probeiq_session` cookie
>   (SameSite=Lax, Secure in production, 14-day TTL), server-side rows in
>   `app/models/` (`User`, `AuthSession`) persisted in **SQLite via SQLAlchemy**
>   (`app/core/database.py`; default `app/data/probeiq.db`). CORS now allows
>   credentials to explicit origins only.
> - **Ownership:** every interview session is bound to the owning user
>   (`owner_user_id`) and enforced server-side via `get_current_user`
>   (`app/api/dependencies.py`).
> - **Config:** `PROBEIQ_DATABASE_URL`, `PROBEIQ_AUTH_COOKIE_NAME`,
>   `PROBEIQ_AUTH_SESSION_TTL_DAYS` added.
> - **Verification:** `uv run pytest` → **180 passed, 3 skipped**; ruff clean;
>   mypy clean in **89** source files; frontend Playwright suite → **51 passed,
>   4 skipped**. The 3 live-LLM tests remain opt-in.
>
> Sections 3 (structure), 4 (API contract), 8 (session store & data), 9 (uv),
> and 14 (security) below describe the pre-auth state and are superseded by the
> above where they conflict.

This document explains the current state of the ProbeIQ backend: what it does,
how it is structured, how the interview workflow operates, how it is run, and
what is still open. Everything below reflects the actual codebase at commit
`057510c` plus the uncommitted UV/Docker changes (pyproject/uv.lock/Dockerfile/
docker-compose.yml).

## 1. What ProbeIQ is

ProbeIQ is a **single-endpoint adaptive interview service**. A candidate is
described by:

- a member profile (name, job role, years of experience, education, status),
- a list of completed "missions" (curriculum days) with pass/skip/attempts,
- aggregate signals (commit days, missions completed, missions first-try).

The service runs a conversational interview that adapts to each answer: it plans
which curriculum topics to probe, decides the next probe (follow-up, new topic,
harder/easier, or complete), and finally produces structured feedback.

The core engine is **deterministic and inspectable** — it always decides WHAT to
probe. An optional LLM (NVIDIA GLM 5.2 through LangChain `ChatNVIDIA`) only
decides HOW to phrase questions and HOW to judge an answer. With the LLM
disabled, template question generation and heuristic evaluation keep the whole
service fully offline.

## 2. Verified stack

| Layer | Version / value | Where |
|---|---|---|
| Python | `>=3.13` (`.python-version` = 3.13; venv uses 3.13.3) | `backend/pyproject.toml` |
| FastAPI | `>=0.141.1` | `pyproject.toml` |
| LangGraph | `>=1.2.10` | `pyproject.toml` |
| langchain | `>=1.3.14` | `pyproject.toml` |
| langchain-nvidia-ai-endpoints | `==1.4.3` | `pyproject.toml` (added; see §9) |
| uv | `0.11.21` | local toolchain + Dockerfile |
| Docker / Compose | `29.6.1` / `v5.2.0` | local |
| ASGI entry point | `app.main:app` | `backend/app/main.py` |
| Env prefix | `PROBEIQ_` | `backend/app/core/config.py` |

## 3. Directory structure

```
backend/
  app/
    main.py                 # FastAPI app factory + global exception handlers; app.main:app
    api/
      dependencies.py       # canonical service/LLM wiring (composition root)
      routes/interview.py   # the single POST /api/interview endpoint
    core/
      config.py             # pydantic-settings Settings (PROBEIQ_ prefix)
      exceptions.py         # ProbeIQError hierarchy
    data/
      candidates.json       # candidate roster loaded by CandidateRepository
      curriculum.json       # curriculum days loaded by CurriculumRepository
    schemas/                # Pydantic models (candidate, session, evaluation, feedback, ...)
    repositories/           # JSON data access + InMemorySessionStore
    services/               # deterministic business logic
    orchestration/          # LangGraph state machine + nodes + decision rules
    agents/                 # question/evaluation/feedback generators (deterministic or LLM)
    prompts/                # LLM prompt builders
    llm/factory.py          # central chat-model factory (ChatNVIDIA / ChatOpenAI)
  tests/                    # 20 test files
  pyproject.toml            # deps + dev group + pytest config
  uv.lock                   # locked environment (78 packages)
  .python-version           # 3.13
  .env                      # local secrets (git-ignored, never committed)
  .env.example              # documented placeholders
  Dockerfile / .dockerignore
  AUDIT_REPORT.md           # Phase 15 audit report (committed)
  audit_verify.py           # deterministic audit driver (committed)
docker-compose.yml          # root-level backend service definition
```

## 4. API contract

There is exactly **one** endpoint, defined in `.opencode/technical-spec.md`:

`POST /api/interview`

- **Start a session**: `{ "sessionId": "s1", "candidate": { ... } }`
- **Send a turn**: `{ "sessionId": "s1", "message": "..." }`

Exactly one of `candidate` (start) or `message` (turn) must be present.
Response is always `{ "reply": string, "done": bool, "feedback": null | {
"summary", "strengths", "gaps", "next" } }`. `done == true` means the interview
completed and `feedback` is populated. The final reply is exactly
`"Interview completed."`.

Errors are JSON `{ "error": code, "detail": message }` with status codes from
the `ProbeIQError` hierarchy (e.g. 404 session not found, 409 session already
exists / already completed, 422 invalid request, 500 internal). The global
exception handlers in `app/main.py` never leak stack traces or credentials.

## 5. Request → workflow (how a turn is processed)

Each HTTP request maps to **one LangGraph invocation** (`StateGraph` compiled
without a checkpointer in `app/orchestration/graph.py`).

Start turn:

```
POST /api/interview (candidate)
  -> analyze_candidate   (candidate signals -> analysis)
  -> plan_interview      (topic plan + strategy, min questions/days)
  -> generate_question   (first question; first turn is always NEW_TOPIC)
  -> END                 (client holds the stored session)
```

Answer turn:

```
POST /api/interview (message)
  -> evaluate_response    (judge the answer)
  -> decide_next_step     (deterministic decision)
     COMPLETE          -> generate_feedback -> END
     FOLLOW_UP / NEW_TOPIC / INCREASE_DIFFICULTY / DECREASE_DIFFICULTY
                       -> generate_question -> END
```

Session state is typed (`InterviewGraphState`) and explicit. The committed
`InterviewSession` is stored in `InMemorySessionStore` **only after a successful
invocation**; a failed run mutates nothing, so turns are safe to retry.

## 6. Deterministic decision engine

All decisions come from `app/orchestration/decision.py` — nothing is random.

- **Quality mapping** (`quality_from_evaluation`): misconceptions or score < 55
  → `weak`; score >= 80 with deep/excellent depth → `strong`; else `adequate`.
- **Probe focus** (`recommended_probe`): misconceptions → fundamental
  understanding; excellent depth → production depth; deep → architecture;
  missing concepts → missing concept; else evidence clarification.
- **Decide** (`decide`):
  - Completes when `question_count >= min_questions (8)` **and**
    `covered_days >= min_covered_days (4)` and the answer is not weak.
  - `hard_max_questions = 16` is a safety valve: it always completes.
  - At `max_questions_per_topic = 3` the engine forces `NEW_TOPIC`.
  - `weak` → decrease difficulty (or follow-up at the foundational floor).
  - `adequate` → follow-up on the same topic.
  - `strong` → increase difficulty once; after 2 strong answers on a topic
    (`STRONG_ANSWERS_BEFORE_TRANSITION = 2`) it transitions to a new topic.
- **Apply** (`apply_decision`): advances topic index / difficulty / follow-up
  index on a deep copy of the committed session; the stored state is never
  mutated in place.

## 7. LLM integration (NVIDIA GLM 5.2)

- Config-driven via `app/core/config.py` (`PROBEIQ_` prefix). Relevant vars
  (see `backend/.env.example`):
  - `PROBEIQ_LLM_ENABLED` (default `false`)
  - `PROBEIQ_LLM_PROVIDER` (`nvidia` | `openai` | `openai-compatible`)
  - `PROBEIQ_LLM_MODEL` (default `z-ai/glm-5.2`)
  - `PROBEIQ_LLM_API_KEY` (SecretStr, **never hardcoded**)
  - `PROBEIQ_LLM_BASE_URL` (empty → NVIDIA default applied by the factory)
  - `PROBEIQ_LLM_TEMPERATURE=1.0`, `PROBEIQ_LLM_TOP_P=1.0`,
    `PROBEIQ_LLM_MAX_TOKENS=16384`, `PROBEIQ_LLM_SEED=42`,
    `PROBEIQ_LLM_MAX_RETRIES=2`
- Central factory `app/llm/factory.py` builds `ChatNVIDIA` for `nvidia` with
  base URL `https://integrate.api.nvidia.com/v1`, pre-registers
  `z-ai/glm-5.2`, and stays **network-free at construction** (no registry call).
- Agents (`app/agents/`) call `llm_utils.invoke_json` with a **single system
  prompt** and a **non-streaming** `chat_model.invoke(...)`. Invalid or missing
  LLM JSON raises `InterviewEngineError` ("no state was changed") so a failed
  call can be retried safely.
- LLM disabled (default / offline): `DeterministicQuestionGenerator`,
  `DeterministicAnswerEvaluator`, `DeterministicFeedbackGenerator` are used.

> Live NVIDIA inference has not been verified from this machine: valid
> chat-completion POSTs to the NVIDIA gateway return zero bytes and time out
> (up to 90 s) via httpx, curl, and raw socket alike, while the gateway responds
> instantly to validation errors. This is an HTTP/API-level issue outside the
> application code. LLM verification is deferred to manual user review.

## 8. Session store & data

- **Store**: `InMemorySessionStore` (process-local, mutex-protected, deep-copies
  on read/write). No persistence across restarts, no cross-process sharing — a
  deliberate hackathon choice; no database.
- **Data**: `candidates.json` and `curriculum.json` under `app/data/`, read by
  `CandidateRepository` / `CurriculumRepository`. Failures raise typed
  `DataLoadError`.
- **PostgreSQL is NOT used**: no DB code exists under `app/`. The `asyncpg`,
  `sqlalchemy`, and `redis` deps in `pyproject.toml` are declared but unused
  placeholders and are a separate follow-up item.

## 9. Dependency management (uv)

- Managed by **uv** (`backend/`): `uv sync --locked` installs from `uv.lock`.
- **P1-1 (fixed):** `langchain-nvidia-ai-endpoints` was imported by the app but
  missing from `pyproject.toml`/`uv.lock`. It is now declared (`==1.4.3`) and
  locked; `uv.lock` grew from 69 to 78 packages. Before the fix, `uv sync`
  silently uninstalled it from the venv.
- Dev-only tools (pytest, pytest-asyncio, ruff, mypy) live in the `dev`
  dependency group and are excluded from the production Docker image.
- Current verification results (all from `backend/`):
  - `uv sync --locked` → Resolved 78 packages, no drift.
  - `uv run pytest` → **172 passed, 3 skipped** (the 3 skips are live-LLM tests,
    deferred per user instruction); 1 pre-existing Starlette/httpx deprecation
    warning.
  - `uv run ruff check app tests` → **All checks passed**.
  - `uv run mypy app tests` → **Success, no issues in 79 source files**.

## 10. Docker

- **`backend/Dockerfile`**: `python:3.13-slim`, installs uv `==0.11.21`, copies
  `pyproject.toml` + `uv.lock` + `.python-version` first, runs
  `uv sync --no-group dev --no-install-project --locked` (production deps only),
  copies `app/`, and runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- **`backend/.dockerignore`**: excludes `.venv`, Python caches, `.git`, `.env`,
  `tests`, audit files, and temp files — the secret key never enters the image.
- **`docker-compose.yml`** (repo root): a single `backend` service built from
  `./backend`, published on port `8000`, with an **optional** `env_file`
  (`./backend/.env`, `required: false`). No postgres service: the application
  does not use a database, so one is deliberately not added.
- Verified locally: `docker build -t probeiq-backend ./backend` succeeds;
  container startup logs "Application startup complete"; `GET /openapi.json`
  returns 200; a deterministic (LLM-disabled) `POST /api/interview` start returns
  a valid `done=false` reply; `docker compose down` tears everything down
  (never `down -v` — that deletes named volumes).
- **Networking note**: inside Compose the backend talks to nothing but its own
  port; localhost-based local dev config is untouched.

## 11. How to run

Local (from `backend/`):
```
uv sync --locked
uv run uvicorn app.main:app --reload     # dev
# or, with LLM enabled: put the key in backend/.env first (copy .env.example)
```
Tests / checks (from `backend/`):
```
uv run pytest
uv run ruff check app tests
uv run mypy app tests
```
Docker:
```
docker build -t probeiq-backend ./backend
docker compose up -d                      # from repo root
docker compose down                       # never down -v
```

## 12. Audit findings & open follow-ups

Phase 15 audit (see `backend/AUDIT_REPORT.md`; 30 PASS / 2 WARN / 0 FAIL in the
deterministic verification driver `backend/audit_verify.py`):

- **P1-1 (FIXED)** — `langchain-nvidia-ai-endpoints` not declared: resolved by
  this UV/Docker task.
- **P1-2 (open)** — `DataLoadError` leaks absolute filesystem paths in 500
  responses; the generic 500 handler itself is safe (no stack traces).
- **P1-3 (open)** — no CORS middleware. Not implemented in this task; deferred
  to a follow-up so it cannot change application behavior here.
- **P2 (open)** — zero observability (no logging in `app/`); four dead files
  (`backend/main.py`, `app/services/interview_service.py`,
  `app/utils/__init__.py`, `app/core/logging.py`); empty root README and missing
  `backend/README.md` (note: `pyproject.toml` still references `README.md`);
  unused `DimensionScores` schema; stale claims in `.opencode/BACKEND.md`
  ("42 tests", "langchain not used") that predate the engine.
- **P3 (open)** — `pip-audit` not run; live NVIDIA path unverifiable from this
  machine.

The one stale audit claim was corrected in this session: `.opencode/technical-spec.md`
**does exist** and defines the `POST /api/interview` contract.

## 13. Current uncommitted changes

Working tree (not yet committed — user has not requested a commit for this
task):
- `backend/pyproject.toml` — added `langchain-nvidia-ai-endpoints==1.4.3`
- `backend/uv.lock` — regenerated (78 packages)
- `backend/Dockerfile`, `backend/.dockerignore`, `docker-compose.yml` — new
- `.opencode/BACKEND.md` — added "Setup & infrastructure (uv + Docker)" section

Already committed: `backend/AUDIT_REPORT.md` and `backend/audit_verify.py`
(commit `057510c`).

## 14. Security posture

- API key is a `SecretStr`; never logged, never printed by the app, never in
  source or Docker/compose files.
- `backend/.env` is git-ignored; `.env.example` holds placeholders only.
- `.dockerignore` keeps `.env` and caches out of the image.
- Follow-up: rotate the NVIDIA API key if it has ever been displayed in terminal
  output (e.g. `docker compose config` interpolates `env_file` values).
