# Technical Specification

This document defines the API contract and submission requirements for the AI Interview Agent.

> **Note (2026-08-09):** The base submission contract below (`POST /api/interview`)
> is unchanged and still defines the interview flow. The running system has a
> deliberate, user-approved extension — **account authentication** — which guards
> the interview endpoint with an HTTP-only session cookie. The extension is
> documented in [Auth extension](#auth-extension) at the end of this file.

---

# HTTP Endpoint

Your agent must expose a single endpoint:

```
POST /api/interview
```

No authentication is required.

> Implemented status: authentication **is** required in the running system
> (see [Auth extension](#auth-extension)). This is an intentional deviation
> from the base spec, requested by the user and applied only to the running
> system; the base contract below is preserved for submission reference.

The endpoint must maintain interview state using the provided `sessionId`.

---

# Interview Flow

## 1. Start Interview

The first request initializes a new interview session.

```json
POST /api/interview

{
  "sessionId": "abc-123",
  "candidate": { ...candidate.json }
}
```

### Expected Response

```json
{
  "reply": "Welcome. Let's begin your interview.",
  "done": false
}
```

---

## 2. Conversation Turn

Every subsequent request contains the candidate's latest response.

```json
{
  "sessionId": "abc-123",
  "message": "..."
}
```

### Expected Response

```json
{
  "reply": "...",
  "done": false
}
```

This continues until the interview is complete.

---

## 3. End Interview

When the interview is complete, return:

```json
{
  "reply": "Interview completed.",
  "done": true,
  "feedback": {
    "summary": "...",
    "strengths": [],
    "gaps": [],
    "next": []
  }
}
```

---

# Feedback Format

The final response must include:

| Field | Type |
|--------|------|
| summary | string |
| strengths | string[] |
| gaps | string[] |
| next | string[] |

Each array should contain concise, actionable points.

---

# Notes

- Use the supplied `sessionId` throughout the interview.
- The interview should remain conversational across multiple requests.
- The candidate object will follow the provided `candidate.json` schema.
- Teams are free to choose any frontend, backend, LLM, framework, or architecture.

---

# Auth extension

Implemented 2026-08-09 (commit `b9a711a`) as a user-approved extension to the
base contract. In the running system, `POST /api/interview` requires a valid
authenticated session; this does not change the interview contract itself.

## Endpoints

| Method & path | Purpose | Auth |
|---|---|---|
| `POST /api/auth/register` | Create an account; sets the session cookie | none |
| `POST /api/auth/login` | Verify credentials; sets the session cookie | none |
| `POST /api/auth/logout` | Revoke the session server-side; clears the cookie | none (idempotent) |
| `GET /api/auth/me` | Return `{ user: {id, email} \| null }`; always 200 | none |
| `POST /api/interview` | The base interview endpoint | **required** |

## Request / response shapes

Register and login both accept `{ "email": string, "password": string }`
(password ≥ 8 chars on register, enforced via 422) and return the user
`{ "id": string, "email": string }` (register returns 201). Logout returns
`{ "detail": "logged out" }`.

Authentication is delivered as an **HTTP-only session cookie**
(`probeiq_session`, `SameSite=Lax`, `Secure` in production, 14-day TTL). The
cookie is set by register/login and cleared by logout.

## Error codes (auth)

| Status | `error` | Trigger |
|---|---|---|
| 401 | `invalid_credentials` | Wrong email/password on login (single generic message) |
| 401 | `not_authenticated` | Missing/invalid/expired session on `POST /api/interview` |
| 403 | `forbidden` | Driving a session started by a different account |
| 409 | `account_already_exists` | Registering with an existing email |

## Ownership

Every interview session started via `POST /api/interview` is bound to the
authenticated user (`session.owner_user_id`). Turn requests are validated
against that owner, so one account can never read or continue another account's
interview. Frontend route guards are UX only — enforcement is server-side.

## Configuration

- `PROBEIQ_DATABASE_URL` — SQLAlchemy URL for auth persistence (default
  `sqlite:///app/data/probeiq.db`).
- `PROBEIQ_AUTH_COOKIE_NAME` — session cookie name (default `probeiq_session`).
- `PROBEIQ_AUTH_SESSION_TTL_DAYS` — session lifetime (default `14`).
