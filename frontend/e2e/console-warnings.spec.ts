import { test, expect } from '@playwright/test'
import {
  slowDownAnswers,
  startInterview,
  submitAnswer,
  waitForReply,
  waitForThinking,
} from './helpers'

test('full journey emits no page errors, no console errors, and no React/accessibility warnings', async ({
  page,
}) => {
  const pageErrors: string[] = []
  const consoleErrors: string[] = []
  const appWarnings: string[] = []
  const allWarnings: string[] = []

  page.on('pageerror', (err) => pageErrors.push(err.message))
  page.on('console', (msg) => {
    const text = msg.text()
    if (msg.type() === 'error') consoleErrors.push(text)
    if (msg.type() === 'warning') {
      allWarnings.push(text)
      // Three/WebGL warnings are vendored three.js / browser GPU driver noise,
      // reported separately; only framework/app warnings gate the test.
      if (/react|accessibility/i.test(text)) appWarnings.push(text)
    }
  })

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
    timeout: 15_000,
  })

  if (allWarnings.length > 0) {
    console.log('[AUDIT] all console warnings:', JSON.stringify(allWarnings, null, 2))
  }

  expect(pageErrors).toEqual([])
  expect(consoleErrors).toEqual([])
  expect(appWarnings).toEqual([])
})
