import { test, expect } from '@playwright/test'
import {
  STRONG_ANSWER,
  attachErrorCollector,
  submitAnswer,
  transcript,
  waitForReply,
  waitForThinking,
} from './helpers'

/**
 * Final end-to-end production simulation: the full 27-step journey exercised in
 * one continuous browser session against the real topology. It is topology
 * agnostic (relative URLs) so it runs identically against the standard e2e
 * servers (:5174 -> :8001) and the production simulation (:5173 -> :8000,
 * PLAYWRIGHT_PREVIEW=1 PLAYWRIGHT_BASE_URL=http://localhost:5173).
 *
 * The journey asserts the complete chain on every leg:
 *   browser -> React -> Zustand -> service -> Axios -> /api -> FastAPI ->
 *   Pydantic -> interview agent -> response -> store -> UI
 * including exactly-one-request guarantees, network/console capture, the
 * Three.js presence surface, failure injection with rollback + retry, and the
 * post-interview report.
 */
test.describe.serial('production simulation', () => {
  test('the full 27-step journey', async ({ page }) => {
    test.setTimeout(120_000)
    const errors = attachErrorCollector(page)

    const failText = 'THIS TURN MUST FAIL and roll back completely.'
    const multiline =
      'Line one of my architecture answer: an ingestion pipeline that normalizes documents.\n' +
      'Line two continues the reasoning with a vector index for hybrid retrieval.\n' +
      'Line three wraps up with the latency versus recall trade-off.'

    const startRequests: Array<{ sessionId: string; candidate: unknown }> = []
    const turnRequests: string[] = []
    const apiResponses: Array<{ url: string; status: number }> = []
    const failedRequests: string[] = []
    page.on('request', (req) => {
      if (!req.url().includes('/api/')) return
      if (req.method() !== 'POST') return
      const post = req.postDataJSON()
      if (post?.candidate) startRequests.push({ sessionId: post.sessionId, candidate: post.candidate })
      else if (post?.message) turnRequests.push(post.message)
    })
    page.on('response', (resp) => {
      if (resp.url().includes('/api/')) apiResponses.push({ url: resp.url(), status: resp.status() })
    })
    page.on('requestfailed', (req) => failedRequests.push(req.url()))

    // Single combined route: answer POSTs are slowed so the thinking phase is
    // observable, and exactly one answer (failText, first submission) is
    // rejected with a 500 to exercise the rollback + retry path.
    let injected = false
    await page.route('**/api/interview', async (route) => {
      const post = route.request().method() === 'POST' ? route.request().postDataJSON() : null
      if (post?.message) {
        if (!injected && post.message === failText) {
          injected = true
          await route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'internal_error', detail: 'simulated production outage' }),
          })
          return
        }
        await new Promise((resolve) => setTimeout(resolve, 300))
      }
      await route.continue()
    })

    const history = transcript(page)

    await test.step('1-2. Landing loads and the CTA leads to /setup', async () => {
      await page.goto('/')
      await expect(page.getByRole('heading', { name: /Prove your skills/i })).toBeVisible()
      const cta = page.getByRole('link', { name: 'Begin interview' })
      await expect(cta).toHaveAttribute('href', '/setup')
      await cta.click()
      await expect(page).toHaveURL(/\/setup/)
    })

    await test.step('3-4. Sample profile is prefilled on /setup', async () => {
      const textarea = page.getByLabel('Candidate profile JSON')
      await textarea.waitFor({ state: 'visible' })
      await expect(textarea).toHaveValue(/Sarah Johnson/)
      await expect(textarea).toHaveValue(/missionsCompleted/)
    })

    await test.step('5-6. Reset keeps /setup usable (no navigation, form remains)', async () => {
      await page.getByRole('button', { name: 'Reset' }).click()
      await expect(page).toHaveURL(/\/setup/)
      await expect(page.getByLabel('Candidate profile JSON')).toBeVisible()
    })

    await test.step('7. Reload the sample profile', async () => {
      await page.getByRole('button', { name: 'Load sample profile' }).click()
      await expect(page.getByLabel('Candidate profile JSON')).toHaveValue(/Sarah Johnson/)
    })

    await test.step('8. Begin interview issues exactly one start request', async () => {
      await page.getByRole('button', { name: 'Begin interview' }).click()
      await page.waitForURL('**/interview', { timeout: 30_000 })
      await expect(page.locator('div.sticky article')).toBeVisible({ timeout: 30_000 })
      expect(startRequests).toHaveLength(1)
      expect(startRequests[0].sessionId).toBeTruthy()
      expect(startRequests[0].candidate).toBeTruthy()
    })

    await test.step('9. Q01 is visible', async () => {
      await expect(page.locator('div.sticky article').getByText('Q01', { exact: true })).toBeVisible({
        timeout: 30_000,
      })
    })

    await test.step('10. Three.js presence canvas is mounted during the interview', async () => {
      await expect(page.locator('canvas')).toHaveCount(1)
    })

    await test.step('11. Submit a multiline answer', async () => {
      const textarea = page.getByLabel('Your answer')
      await textarea.fill(multiline)
      await expect(textarea).toHaveValue(multiline)
      await page.getByRole('button', { name: 'Submit' }).click()
    })

    await test.step('12-13. Thinking indicator appears while the answer is processed', async () => {
      await waitForThinking(page)
    })

    await test.step('14-15. Presence canvas persists during the thinking phase', async () => {
      await expect(page.getByRole('status')).toContainText(/analyzing/i)
      await expect(page.locator('canvas')).toHaveCount(1)
    })

    await test.step('16. Exactly one turn POST; the answer lands in the transcript', async () => {
      await waitForReply(page)
      expect(turnRequests).toHaveLength(1)
      expect(turnRequests[0]).toBe(multiline)
      await expect(history).toContainText('Line two continues the reasoning')
    })

    await test.step('17. Next question arrives', async () => {
      await expect(page.locator('div.sticky article').getByText('Q02', { exact: true })).toBeVisible({
        timeout: 30_000,
      })
    })

    await test.step('18. Submit a second answer', async () => {
      await submitAnswer(page, STRONG_ANSWER)
      await waitForThinking(page)
      await waitForReply(page)
    })

    await test.step('19-20. Backend failure injection: alert + rollback, no phantom message', async () => {
      const textarea = page.getByLabel('Your answer')
      await textarea.fill(failText)
      await page.getByRole('button', { name: 'Submit' }).click()

      await expect(page.getByRole('alert')).toBeVisible({ timeout: 15_000 })
      await expect(page.getByRole('alert')).toContainText(/try again|failed|error/i)
      // Rollback restores the pre-answer state: the failed text is not in the
      // transcript and the composer keeps it so nothing is lost.
      await expect(history).not.toContainText(failText)
      await expect(textarea).toHaveValue(failText)
    })

    await test.step('21. Retry succeeds with exactly one copy of the answer', async () => {
      await page.getByRole('button', { name: 'Try again' }).click()
      await waitForReply(page)
      await expect(history.getByText(failText, { exact: true })).toHaveCount(1)
      expect(turnRequests.filter((m) => m === failText)).toHaveLength(2) // one rejected, one successful
    })

    await test.step('22-23. Drive the interview to completion', async () => {
      const isComplete = () => page.url().includes('/complete')
      for (let i = 0; i < 18 && !isComplete(); i++) {
        await submitAnswer(page)
        await waitForThinking(page)
        await Promise.race([
          waitForReply(page).catch(() => undefined),
          page.waitForURL('**/complete', { timeout: 30_000 }).catch(() => undefined),
        ])
      }
      await expect(page).toHaveURL(/\/complete/, { timeout: 30_000 })
    })

    await test.step('24-25. /complete renders the backend feedback report', async () => {
      await expect(
        page.getByRole('heading', { name: "You've finished your technical interview." }),
      ).toBeVisible({ timeout: 15_000 })
      await expect(page.getByRole('heading', { name: 'Your post-interview report' })).toBeVisible({
        timeout: 15_000,
      })
      await expect(page.getByText(/Interview complete:/)).toBeVisible()
      await expect(page.getByRole('heading', { name: 'Summary' })).toBeVisible()
      await expect(page.getByRole('heading', { name: 'What you demonstrated' })).toBeVisible()
      await expect(page.getByRole('heading', { name: 'Next steps' })).toBeVisible()
      // The Interview page (with its composer + timer) is unmounted.
      await expect(page.getByLabel('Your answer')).toHaveCount(0)
    })

    await test.step('26. New interview confirms and returns to a fresh /setup', async () => {
      page.on('dialog', (dialog) => dialog.accept())
      await page.getByRole('button', { name: 'New interview' }).click()
      await expect(page).toHaveURL(/\/setup/)
      await expect(page.getByLabel('Candidate profile JSON')).toBeVisible()
      await expect(page.getByLabel('Candidate profile JSON')).toHaveValue(/Sarah Johnson/)
    })

    await test.step('27. A second interview starts fresh at Q01 with a new session', async () => {
      await page.getByRole('button', { name: 'Begin interview' }).click()
      await page.waitForURL('**/interview', { timeout: 30_000 })
      await expect(page.locator('div.sticky article').getByText('Q01', { exact: true })).toBeVisible({
        timeout: 30_000,
      })
      expect(startRequests).toHaveLength(2)
      expect(startRequests[1].sessionId).not.toBe(startRequests[0].sessionId)
    })

    await test.step('Network capture: every /api response is 2xx except the single injected 500', async () => {
      expect(apiResponses.length).toBeGreaterThan(0)
      const nonOk = apiResponses.filter((r) => r.status >= 400)
      expect(nonOk).toHaveLength(1)
      expect(nonOk[0].status).toBe(500)
      expect(failedRequests).toEqual([])
    })

    await test.step('Browser console: zero app errors (only the expected injected-500 log)', async () => {
      // The one deliberate 500 makes the browser itself log
      // "Failed to load resource ... 500" — that is unavoidable browser
      // behavior for any 500 and is expected here. Everything else must be
      // clean: no React errors, no network failures, no Three.js errors.
      const unexpected = errors.filter((e) => !e.includes('the server responded with a status of 500'))
      expect(unexpected).toEqual([])
      expect(errors.filter((e) => e.includes('the server responded with a status of 500'))).toHaveLength(1)
    })
  })
})
