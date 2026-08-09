import { expect, type Page } from '@playwright/test'

/** Mirrors backend test STRONG_ANSWER — advances the deterministic engine. */
export const STRONG_ANSWER =
  'I would design this in three layers: an ingestion pipeline that normalizes documents ' +
  'into retrieval-friendly chunks with metadata, a vector index with hybrid retrieval that ' +
  'fuses dense and sparse signals, and a generation step that is grounded strictly in the ' +
  'retrieved context. The main trade-off is recall versus latency, so I would benchmark chunk ' +
  'size and index layout before locking the design.'

/** Matches backend RegisterRequest password policy (min 8 chars). */
export const TEST_PASSWORD = 'S3cure!Pass123'

/**
 * Registers a fresh account through the API so the context holds a valid
 * session cookie. `page.request` shares the browser context's cookie jar, so
 * the HTTP-only session cookie set here is sent with every subsequent page
 * navigation/fetch.
 */
export async function signIn(page: Page): Promise<void> {
  const email = `e2e-${Date.now()}-${Math.random().toString(36).slice(2)}@example.com`
  const response = await page.request.post('/api/auth/register', {
    data: { email, password: TEST_PASSWORD },
  })
  expect(response.ok(), `signIn register failed: ${response.status()}`).toBeTruthy()
}

export async function startInterview(page: Page): Promise<void> {
  await signIn(page)
  await page.goto('/setup')
  await page.getByLabel('Candidate profile JSON').waitFor({ state: 'visible' })
  await page.getByRole('button', { name: 'Begin interview' }).click()
  await page.waitForURL('**/interview')
  await expect(page.locator('div.sticky article')).toBeVisible({ timeout: 30_000 })
}

export async function submitAnswer(page: Page, text: string = STRONG_ANSWER): Promise<void> {
  const textarea = page.getByLabel('Your answer')
  const submit = page.getByRole('button', { name: 'Submit' })
  await textarea.fill(text)
  await expect(textarea).toHaveValue(text)
  await expect(submit).toBeEnabled()
  await submit.click()
}

/** Waits for the thinking indicator ("The interviewer is analyzing your answer"). */
export async function waitForThinking(page: Page): Promise<void> {
  await expect(page.getByRole('status')).toContainText(/analyzing/i, { timeout: 15_000 })
}

/**
 * Waits for the current turn to settle: thinking indicator gone and the composer
 * (textarea) back. The composer is intentionally cleared on success, so the
 * Submit button being disabled is expected — it is NOT a ready signal.
 */
export async function waitForReply(page: Page): Promise<void> {
  await expect(page.getByRole('status')).toBeHidden({ timeout: 30_000 })
  await expect(page.getByLabel('Your answer')).toBeVisible({ timeout: 15_000 })
}

/** The transcript history region on the interview page. */
export function transcript(page: Page) {
  return page.getByRole('region', { name: 'Interview transcript so far' })
}

/** Resolves true when the document has no horizontal overflow. */
export async function hasHorizontalOverflow(page: Page): Promise<boolean> {
  return page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  )
}

/** Attaches pageerror + console-error listeners; returns the collected messages. */
export function attachErrorCollector(page: Page): string[] {
  const errors: string[] = []
  page.on('pageerror', (err) => errors.push(`pageerror: ${err.message}`))
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(`console.error: ${msg.text()}`)
  })
  return errors
}

/**
 * Delays answer POSTs (requests carrying a `message`) so the thinking phase is
 * observable and each turn settles deterministically. The start request is
 * passed through untouched.
 */
export async function slowDownAnswers(page: Page, delayMs = 350): Promise<void> {
  await page.route('**/api/interview', async (route) => {
    const post = route.request().method() === 'POST' ? route.request().postDataJSON() : null
    if (post?.message) await new Promise((resolve) => setTimeout(resolve, delayMs))
    await route.continue()
  })
}
