import { test, expect } from '@playwright/test'
import {
  attachErrorCollector,
  slowDownAnswers,
  startInterview,
  submitAnswer,
  waitForReply,
  waitForThinking,
} from './helpers'
import type { Page } from '@playwright/test'

async function runToCompletion(page: Page): Promise<void> {
  await slowDownAnswers(page, 300)
  await startInterview(page)
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
}

test('direct /complete without a session redirects to /setup', async ({ page }) => {
  await page.goto('/complete')
  await expect(page).toHaveURL(/\/setup/, { timeout: 15_000 })
})

test('completion transition reveals the report from backend feedback', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await runToCompletion(page)
  await expect(
    page.getByRole('heading', { name: "You've finished your technical interview." }),
  ).toBeVisible({ timeout: 15_000 })
  await expect(page.getByRole('heading', { name: 'Your post-interview report' })).toBeVisible({
    timeout: 15_000,
  })
  await expect(page.getByRole('heading', { name: 'Summary' })).toBeVisible()
  await expect(page.getByText(/Interview complete:/)).toBeVisible()
  await expect(page.getByRole('heading', { name: 'What you demonstrated' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Next steps' })).toBeVisible()
  expect(errors).toEqual([])
})

test('focus moves to the report heading after the transition', async ({ page }) => {
  await runToCompletion(page)
  await expect(page.getByRole('heading', { name: 'Your post-interview report' })).toBeFocused({
    timeout: 15_000,
  })
})

test('new interview resets and returns to a fresh setup', async ({ page }) => {
  await runToCompletion(page)
  page.on('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: 'New interview' }).click()
  await expect(page).toHaveURL(/\/setup/)
  await expect(page.getByLabel('Candidate profile JSON')).toBeVisible()

  await page.getByRole('button', { name: 'Begin interview' }).click()
  await page.waitForURL('**/interview', { timeout: 30_000 })
  await expect(page.locator('div.sticky article').getByText('Q01', { exact: true })).toBeVisible({
    timeout: 30_000,
  })
})

test('missing optional feedback renders a graceful fallback', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await page.route('**/api/interview', async (route) => {
    const post = route.request().method() === 'POST' ? route.request().postDataJSON() : null
    if (post?.message) await new Promise((resolve) => setTimeout(resolve, 300))
    const response = await route.fetch()
    const body = await response.json()
    if (body.done === true) delete body.feedback
    await route.fulfill({ response, json: body })
  })
  await startInterview(page)
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
  await expect(page.getByText('No report was returned for this session.')).toBeVisible({
    timeout: 15_000,
  })
  expect(errors).toEqual([])
})

test('reduced motion reveals the report immediately without the debrief phase', async ({
  browser,
}) => {
  const context = await browser.newContext({ reducedMotion: 'reduce' })
  const page = await context.newPage()
  await slowDownAnswers(page, 300)
  await startInterview(page)
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
  await expect(page.getByRole('heading', { name: 'Your post-interview report' })).toBeVisible({
    timeout: 10_000,
  })
  await expect(page.getByText('Preparing your debrief')).toBeHidden()
  await context.close()
})
