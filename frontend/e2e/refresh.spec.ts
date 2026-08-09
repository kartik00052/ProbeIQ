import { test, expect } from '@playwright/test'
import {
  slowDownAnswers,
  startInterview,
  submitAnswer,
  waitForReply,
  waitForThinking,
} from './helpers'

test('refresh during setup keeps setup with the prefilled form', async ({ page }) => {
  await page.goto('/setup')
  await page.reload()
  await expect(page).toHaveURL(/\/setup/)
  await expect(page.getByLabel('Candidate profile JSON')).toHaveValue(/Sarah Johnson/)
})

test('refresh during interview returns to setup (session is process-local)', async ({ page }) => {
  await slowDownAnswers(page)
  await startInterview(page)
  await page.reload()
  await expect(page).toHaveURL(/\/setup/, { timeout: 15_000 })
})

test('refresh after completion returns to setup', async ({ page }) => {
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
  await page.reload()
  await expect(page).toHaveURL(/\/setup/, { timeout: 15_000 })
})
