import { test, expect } from '@playwright/test'
import {
  attachErrorCollector,
  slowDownAnswers,
  startInterview,
  submitAnswer,
  waitForReply,
  waitForThinking,
} from './helpers'

test('full interview completes and the report renders', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await slowDownAnswers(page, 300)
  await startInterview(page)

  const isComplete = () => page.url().includes('/complete')
  let turns = 0
  for (let i = 0; i < 18 && !isComplete(); i++) {
    turns += 1
    await submitAnswer(page)
    // The thinking indicator must visibly appear before we wait for the reply.
    // Waiting only for "status hidden" can resolve in the pre-render gap right
    // after the click, letting the next turn type over an in-flight turn.
    await waitForThinking(page)
    await Promise.race([
      waitForReply(page).catch(() => undefined),
      page.waitForURL('**/complete', { timeout: 30_000 }).catch(() => undefined),
    ])
  }

  await expect(page).toHaveURL(/\/complete/, { timeout: 30_000 })
  expect(turns).toBeLessThanOrEqual(17)

  await expect(
    page.getByRole('heading', { name: "You've finished your technical interview." }),
  ).toBeVisible({ timeout: 15_000 })

  await expect(page.getByRole('heading', { name: 'Post-interview report' })).toBeVisible({
    timeout: 15_000,
  })

  await expect(page.getByText(/Interview complete:/)).toBeVisible()
  expect(errors).toEqual([])
})
