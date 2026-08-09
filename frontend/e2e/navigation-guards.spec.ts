import { test, expect } from '@playwright/test'
import {
  attachErrorCollector,
  slowDownAnswers,
  startInterview,
  submitAnswer,
  waitForReply,
  waitForThinking,
} from './helpers'

test('direct /interview navigation without a session redirects to /login', async ({ page }) => {
  await page.goto('/interview')
  await expect(page).toHaveURL(/\/login/, { timeout: 15_000 })
})

test('browser Back from /complete returns to /complete, never an active composer', async ({
  page,
}) => {
  const errors = attachErrorCollector(page)
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

  await page.goBack()
  await expect(page).toHaveURL(/\/complete/, { timeout: 15_000 })
  await expect(page.getByLabel('Your answer')).toHaveCount(0)
  expect(errors).toEqual([])
})
