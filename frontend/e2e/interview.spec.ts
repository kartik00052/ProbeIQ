import { test, expect } from '@playwright/test'
import {
  attachErrorCollector,
  slowDownAnswers,
  startInterview,
  submitAnswer,
  transcript,
  waitForReply,
  waitForThinking,
} from './helpers'

test('full turn cycle: question, thinking, next question, transcript growth', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await slowDownAnswers(page)
  await startInterview(page)

  const questionCard = page.locator('div.sticky article')
  await expect(questionCard.getByText('Q01', { exact: true })).toBeVisible()

  const history = transcript(page)
  const initialCount = await history.locator('p').count()

  await submitAnswer(page)

  await waitForThinking(page)
  await expect(page.getByRole('button', { name: 'Thinking…' })).toBeDisabled()

  await waitForReply(page)

  await expect(questionCard.getByText('Q02', { exact: true })).toBeVisible({ timeout: 15_000 })
  const afterCount = await history.locator('p').count()
  expect(afterCount).toBeGreaterThan(initialCount)

  const historyText = (await history.innerText()).toLowerCase()
  expect(historyText).toContain('you')
  expect(historyText).toContain('interviewer')

  expect(errors).toEqual([])
})

test('composer is cleared after a successful reply', async ({ page }) => {
  await slowDownAnswers(page)
  await startInterview(page)
  await submitAnswer(page)
  await waitForReply(page)
  await expect(page.getByLabel('Your answer')).toHaveValue('')
})
