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

function timer(page: Page) {
  return page.locator('header span.font-mono.text-sm')
}

function secondsAfter(value: string, other: string): boolean {
  return value > other
}

test('timer runs while the interview is active', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await slowDownAnswers(page)
  await startInterview(page)
  const t = timer(page)
  await expect(t).toHaveText('00:00')
  await page.waitForTimeout(2100)
  const after = await t.textContent()
  expect(after).not.toBe('00:00')
  expect(secondsAfter(after as string, '00:00')).toBe(true)
  expect(errors).toEqual([])
})

test('timer pauses during thinking and resumes after the reply', async ({ page }) => {
  await slowDownAnswers(page, 6000)
  await startInterview(page)
  const t = timer(page)
  await expect(t).toHaveText('00:00')

  await submitAnswer(page)
  await waitForThinking(page)
  await page.waitForTimeout(2500)
  const frozen = await t.textContent()
  await page.waitForTimeout(2000)
  expect(await t.textContent()).toBe(frozen)

  await waitForReply(page)
  await page.waitForTimeout(2100)
  expect(await t.textContent()).not.toBe(frozen)
})

test('timer is gone after completion (Interview unmounts)', async ({ page }) => {
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
  await expect(timer(page)).toHaveCount(0)
  expect(errors).toEqual([])
})

test('curriculum progress reflects the candidate missions only', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await slowDownAnswers(page)
  await startInterview(page)
  const coverage = page.getByRole('region', { name: 'Curriculum coverage' })
  await expect(coverage).toBeVisible()
  for (const day of ['07', '08', '10', '16', '22', '29', '31']) {
    await expect(coverage.getByText(day, { exact: true })).toBeVisible()
  }
  await expect(coverage.getByText('01', { exact: true })).toHaveCount(0)
  expect(errors).toEqual([])
})
