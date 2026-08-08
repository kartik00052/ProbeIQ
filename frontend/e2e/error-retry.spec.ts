import { test, expect } from '@playwright/test'
import { startInterview, submitAnswer, transcript, waitForReply } from './helpers'

test('failed answer is rolled back and recoverable via retry', async ({ page }) => {
  await startInterview(page)
  const history = transcript(page)

  await page.route('**/api/interview', async (route) => {
    const post = route.request().method() === 'POST' ? route.request().postDataJSON() : null
    if (post?.message) await route.abort('failed')
    else await route.continue()
  })

  const answerText = 'This answer should roll back.'
  await submitAnswer(page, answerText)

  await expect(page.getByRole('alert')).toBeVisible({ timeout: 15_000 })
  // Rollback restores the pre-answer state: the history region is empty and
  // therefore not rendered, and the failed answer stays in the composer.
  await expect(history).toHaveCount(0)
  await expect(page.getByLabel('Your answer')).toHaveValue(answerText)

  await page.unroute('**/api/interview')
  await page.getByRole('button', { name: 'Try again' }).click()

  await waitForReply(page)
  await expect(history).toContainText(answerText)
})
