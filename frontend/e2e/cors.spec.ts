import { test, expect } from '@playwright/test'

/**
 * Production frontend -> backend/CORS verification.
 *
 * The normal e2e suite talks to the backend through the Vite dev proxy (same
 * origin), which bypasses CORS entirely. This spec exercises the real
 * CORSMiddleware by making genuine cross-origin requests from a page served at
 * the production origin (:5173) directly to the backend at :8000 — the exact
 * topology a separately-hosted production frontend would use.
 *
 * It only runs in the production-simulation topology
 * (PLAYWRIGHT_PREVIEW=1 PLAYWRIGHT_BASE_URL=http://localhost:5173 with the
 * backend on :8000); it is skipped in the standard :5174/:8001 suite where the
 * :5173 origin is not in the allowlist.
 */

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:5174'
const BACKEND_PORT = process.env.PROBEIQ_E2E_API_PORT ?? '8000'
const BACKEND = `http://127.0.0.1:${BACKEND_PORT}`

const START_PAYLOAD = {
  sessionId: 'cors-prod-sim-1',
  candidate: {
    member: {
      id: 'CORS-1',
      name: 'Ada Lovelace',
      jobRole: 'ML Engineer',
      yearsExperience: 5,
      education: 'PhD',
      status: 'ACTIVE',
    },
    missions: [{ day: 1, title: 'Intro to AI', passed: true, skipped: null, attempts: 1 }],
    signals: { commitDays: 1, missionsCompleted: 1, missionsFirstTry: 1 },
  },
}

test.describe('production CORS path', () => {
  test.skip(!BASE_URL.includes('5173'), 'production CORS check runs on the :5173 -> :8000 topology only')

  test('preflight for the allowed origin succeeds with CORS headers', async ({ request }) => {
    const res = await request.fetch(`${BACKEND}/api/interview`, {
      method: 'OPTIONS',
      headers: {
        Origin: 'http://localhost:5173',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type',
      },
    })
    expect(res.status()).toBe(200)
    expect(res.headers()['access-control-allow-origin']).toBe('http://localhost:5173')
    expect(res.headers()['access-control-allow-methods']).toContain('POST')
  })

  test('a real cross-origin POST from the production page passes CORS (authenticated guard applies)', async ({
    page,
  }) => {
    const sessionId = `cors-prod-sim-${Date.now()}`
    const payload = { ...START_PAYLOAD, sessionId }
    let acao: string | undefined
    let corsStatus: number | undefined
    page.on('response', (resp) => {
      if (resp.url().startsWith(`${BACKEND}/api/interview`)) {
        corsStatus = resp.status()
        acao = resp.headers()['access-control-allow-origin']
      }
    })

    await page.goto('/')
    // The browser runs a genuine cross-origin request with a CORS preflight.
    // If the middleware were misconfigured the fetch below would reject with a
    // TypeError and page.evaluate would throw; resolving with a readable JSON
    // body is itself proof the preflight and response passed browser CORS.
    // Since the interview endpoint is now behind authentication, the anonymous
    // request resolves to 401 not_authenticated — which still requires the
    // CORS headers to be readable by JS.
    const result = await page.evaluate(
      async ({ target, payload }) => {
        const res = await fetch(`${target}/api/interview`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        return { status: res.status, body: await res.json() }
      },
      { target: BACKEND, payload },
    )
    expect(result.status).toBe(401)
    expect(result.body.error).toBe('not_authenticated')
    expect(result.body.detail).toBeTruthy()
    // The access-control-allow-origin header is not exposed to JS (not listed
    // in Access-Control-Expose-Headers), so assert it at the network layer.
    expect(corsStatus).toBe(401)
    expect(acao).toBe('http://localhost:5173')
  })

  test('a disallowed origin gets no CORS headers', async ({ request }) => {
    const res = await request.fetch(`${BACKEND}/api/interview`, {
      method: 'OPTIONS',
      headers: {
        Origin: 'http://localhost:9999',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type',
      },
    })
    expect(res.headers()['access-control-allow-origin']).toBeUndefined()
  })

  test('simple GET from a disallowed origin also omits CORS headers', async ({ request }) => {
    const res = await request.fetch(`${BACKEND}/openapi.json`, {
      headers: { Origin: 'http://localhost:9999' },
    })
    expect(res.status()).toBe(200)
    expect(res.headers()['access-control-allow-origin']).toBeUndefined()
  })
})
