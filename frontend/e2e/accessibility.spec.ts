import { test, expect } from '@playwright/test'
import {
  attachErrorCollector,
  slowDownAnswers,
  startInterview,
  signIn,
  submitAnswer,
  waitForReply,
} from './helpers'

test('question card is aria-live and thinking state is announced', async ({ page }) => {
  await slowDownAnswers(page)
  await startInterview(page)
  await expect(page.locator('div.sticky article')).toHaveAttribute('aria-live', 'polite')
  await submitAnswer(page)
  await expect(page.getByRole('status')).toContainText(/analyzing/i)
  await waitForReply(page)
})

test('answer input is labelled and submit is disabled while empty', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await startInterview(page)
  const textarea = page.getByLabel('Your answer')
  await expect(textarea).toBeVisible()
  await expect(textarea).toHaveAttribute('aria-label', 'Your answer')
  await expect(page.getByRole('button', { name: 'Submit' })).toBeDisabled()
  expect(errors).toEqual([])
})

test('keyboard-only navigation reaches setup controls', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await signIn(page)
  await page.goto('/setup')
  const textarea = page.getByLabel('Candidate profile JSON')
  await textarea.focus()
  await expect(textarea).toBeFocused()
  await page.keyboard.press('Tab')
  await page.keyboard.press('Tab')
  await expect(page.getByRole('button', { name: 'Begin interview' })).toBeFocused()
  expect(errors).toEqual([])
})

test('reduced motion keeps the interface usable with a static presence', async ({ browser }) => {
  const context = await browser.newContext({ reducedMotion: 'reduce' })
  const page = await context.newPage()
  await signIn(page)
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /Prove your skills/i })).toBeVisible()
  await expect(page.locator('canvas')).toHaveCount(0)
  await page.getByRole('link', { name: 'Begin interview' }).click()
  await expect(page.getByLabel('Candidate profile JSON')).toBeVisible()
  await context.close()
})

test('long answer submits without breaking the composer', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await slowDownAnswers(page)
  await startInterview(page)
  const longAnswer = 'A'.repeat(1800)
  await submitAnswer(page, longAnswer)
  await waitForReply(page)
  await expect(page.getByRole('region', { name: 'Interview transcript so far' })).toContainText(
    'A'.repeat(16),
  )
  expect(errors).toEqual([])
})
