# ProbeIQ Backend Audit Report — Phase 15 Final

Date: 2026-08-08 · Scope: `backend/` @ commit `1bfb1b5` · Method: deterministic-engine verification + code review (Phases 2/3/8 LLM-related items deferred to manual review per user)

## Summary

| Metric | Result |
|---|---|
| Total checks | 32 deterministic checks + 172 unit tests |
| Deterministic checks | **30 PASS / 2 WARN / 0 FAIL** |
| Unit tests | **172 passed, 3 skipped** (live-LLM opt-in), 6.75s |
| Lint (ruff) | clean (`All checks passed`) |
| Types (mypy) | clean (`Success: no issues found in 79 source files`) |
| Deterministic latency | p50 ≈ 5ms/turn; 8 turns (strong) / 16 turns (weak) to completion |

## Phase Checklist

- **P1 Repository inspection — PASS.** No duplicate endpoints; single `POST /api/interview` router. 4 stale git-tracked files not imported anywhere: `backend/main.py` (stub), `backend/app/services/interview_service.py` (0 B), `backend/app/utils/__init__.py` (0 B), `backend/app/core/logging.py` (0 B). Root README is empty; `technical-spec.md` referenced in docstrings **does not exist**.
- **P2 NVIDIA GLM 5.2 integration — DEFERRED (manual).** Verified structurally: `get_llm()` constructs `ChatNVIDIA` network-free (model pre-registered), key handled via `SecretStr`, never logged. Attempted live run on this machine: `GET /v1/models` succeeds (200, 0.4s) but `POST /chat/completions` times out (ReadTimeout) — known DNS64/NAT64 network issue. **Live path unverified on this machine.**
- **P3 Intelligence split — DEFERRED (manual).** Structurally verified: deterministic controller (`decision.py`) decides WHAT (FOLLOW_UP/NEW_TOPIC/INCREASE/DECREASE/COMPLETE); LLM only phrases HOW.
- **P4 Personalization — PASS.** CAND-001 vs CAND-011: different first questions, `strong_days=[7,8,16,31]` vs `[2]`, both complete in 8 turns.
- **P5 Adaptive behavior — PASS.** Observed decision sequence `WEAK→DECREASE_DIFFICULTY → WEAK→FOLLOW_UP → ADEPT→NEW_TOPIC → ADEPT→FOLLOW_UP → STRONG→FOLLOW_UP → STRONG→NEW_TOPIC → STRONG→INCREASE_DIFFICULTY`. `quality_from_evaluation`: 90/deep→strong, 70/moderate→adequate, 20/misconception→weak.
- **P6 Minimum requirements — PASS.** Strong interview: 8 questions ≥ 8, 4 covered days ≥ 4, ≤ 16 hard max. Weak-only interview terminates at hard max (16 questions).
- **P7 Conversation context — PASS.** Follow-ups stay on topic (`Embeddings Explained` → same), `follow_up_index=1`, history retained (2 questions/1 response/1 evaluation), sessions independent, deterministic replay identical.
- **P8 Structured LLM output — DEFERRED (manual).** Schemas verified (`Evaluation` depth literals `none/shallow/moderate/deep/excellent`).
- **P9 Failure handling — PASS.** Unknown session → 404; 8-thread concurrent store ops, 0 errors; flaky-evaluator failure leaves committed session untouched (byte-identical) and retry advances correctly.
- **P10 API contract — PASS (9/9).** Start (done=False, feedback=None, reply set); turn (done=False); 404/422/400 error codes with exact `error` strings; completion (`"Interview completed."`, feedback `{summary, strengths, gaps, next}`); questions grounded to curriculum.
- **P11 Security — PASS with 2 findings.** Key safe (SecretStr, never in logs/errors; `.env` git-ignored; no hardcoded secrets; generic 500 handler hides internals). Findings below.
- **P12 Test quality — PASS.** 172 passed / 3 skipped; ruff + mypy clean.
- **P13 Performance — WARN.** Deterministic path p50 ≈ 5ms/turn (deterministic only; LLM path unmeasured — deferred). No load test; in-memory store single-process.
- **P14 Database decision — PASS.** Keep `InMemorySessionStore` + JSON data files for the hackathon; no PostgreSQL/Redis. Postgres only as a future extension (deps already present but unused — see P1).
- **P15 Final report — THIS DOCUMENT.**

## Findings

### P0 (must fix before frontend integration)
None.

### P1 (high)
1. **`langchain-nvidia-ai-endpoints` missing from `pyproject.toml` / `uv.lock`.** Code imports `ChatNVIDIA` (`app/api/dependencies.py:1`, `app/llm/factory.py:29`) but the dependency is undeclared; only present in `.venv`. A clean `uv sync` on a fresh machine breaks. (pyproject currently declares unused `asyncpg`, `redis`, `sqlalchemy`.)
2. **`DataLoadError` leaks absolute filesystem paths in 500 responses** (verified via API): `{"error":"data_load_error","detail":"failed to load candidate data from C:/Users/karti/Downloads/ProbeIQ/backend/app/data/candidates.json: ..."}`. `main.py` surfaces `exc.detail` verbatim for domain errors. Sanitize server paths before returning.
3. **No CORS middleware configured.** Frontend on a different origin/port will be blocked by the browser. Add a scoped CORS allowlist.

### P2 (medium)
4. Zero observability: no `print`/`logging` anywhere in `app/`. Add structured logging (start/turn/complete, per-node timing) — no keys ever.
5. Stale files (4 dead modules + empty root README + missing `backend/README.md` referenced by `pyproject.toml`) — document or remove in the freeze commit.
6. `DimensionScores` schema exists but is unused by `Evaluation` (no `dimensions` field) — intended Phase 6 explainability is not wired into the API.
7. `technical-spec.md` referenced in comments/spec does not exist anywhere in the repo.

### P3 (low)
8. `test_hackathon_verification.py` from a prior session is no longer present (was never committed). The deterministic phases were re-verified via `audit_verify.py` (untracked, 30 PASS). Consider committing it as regression coverage.
9. `pip-audit` not installed; dependency vulnerability scan not run.

## Recommended actions (in order)
1. Fix P1.1: declare the nvidia dep in `pyproject.toml` + `uv lock`.
2. Fix P1.2: sanitize `DataLoadError` (and any path-bearing detail) before exposing.
3. Fix P1.3: add CORS middleware for the frontend origin.
4. Commit `audit_verify.py` (or equivalent) as a deterministic regression suite.
5. (Manual) verify live GLM 5.2 on a machine with working network; validate structured LLM output end-to-end.
6. Dockerize per plan; freeze backend.
