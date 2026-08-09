import { test, expect } from '@playwright/test'
import { attachErrorCollector, signIn } from './helpers'

test('load sample profile restores the sample JSON', async ({ page }) => {
  await signIn(page)
  await page.goto('/setup')
  const textarea = page.getByLabel('Candidate profile JSON')
  await textarea.fill('{ "broken": true }')
  await page.getByRole('button', { name: 'Load sample profile' }).click()
  await expect(textarea).toHaveValue(/Sarah Johnson/)
  await expect(textarea).toHaveValue(/missionsCompleted/)
})

test('reset keeps setup usable and does not navigate', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await signIn(page)
  await page.goto('/setup')
  await page.getByRole('button', { name: 'Reset' }).click()
  await expect(page).toHaveURL(/\/setup/)
  await expect(page.getByLabel('Candidate profile JSON')).toBeVisible()
  expect(errors).toEqual([])
})

test('valid custom candidate JSON starts the interview', async ({ page }) => {
  const custom = JSON.stringify({
    member: {
      id: 'X-1',
      name: 'Ada Lovelace',
      jobRole: 'ML Engineer',
      yearsExperience: 5,
      education: 'PhD',
      status: 'ACTIVE',
    },
    missions: [{ day: 1, title: 'Intro to AI', passed: true, skipped: null, attempts: 1 }],
    signals: { commitDays: 1, missionsCompleted: 1, missionsFirstTry: 1 },
  })
  await signIn(page)
  await page.goto('/setup')
  await page.getByLabel('Candidate profile JSON').fill(custom)
  await page.getByRole('button', { name: 'Begin interview' }).click()
  await page.waitForURL('**/interview')
  await expect(page.locator('div.sticky article')).toBeVisible({ timeout: 30_000 })
})

test('malformed candidate data shows an inline error and stays on setup', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await signIn(page)
  await page.goto('/setup')
  const malformed = JSON.stringify({
    member: {
      id: '',
      name: '',
      jobRole: '',
      yearsExperience: -1,
      education: '',
      status: '',
    },
    missions: [{ day: 0, title: '', passed: null, skipped: null, attempts: 0 }],
    signals: { commitDays: -1, missionsCompleted: -1, missionsFirstTry: -1 },
  })
  await page.getByLabel('Candidate profile JSON').fill(malformed)
  await page.getByRole('button', { name: 'Begin interview' }).click()
  await expect(page.locator('.text-danger')).toBeVisible()
  await expect(page).toHaveURL(/\/setup/)
  expect(errors).toEqual([])
})

test('failed start shows an error and retry recovers with a second request', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (err) => pageErrors.push(err.message))
  await signIn(page)
  await page.goto('/setup')
  let startCalls = 0
  await page.route('**/api/interview', async (route) => {
    const post = route.request().method() === 'POST' ? route.request().postDataJSON() : null
    if (post?.candidate) {
      startCalls += 1
      if (startCalls === 1) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'boom', detail: 'server error' }),
        })
        return
      }
    }
    await route.continue()
  })

  await page.getByRole('button', { name: 'Begin interview' }).click()
  await expect(page.getByRole('alert')).toBeVisible({ timeout: 15_000 })
  await expect(page).toHaveURL(/\/setup/)

  await page.getByRole('button', { name: 'Try again' }).click()
  await page.waitForURL('**/interview', { timeout: 30_000 })
  await expect(page.locator('div.sticky article')).toBeVisible({ timeout: 30_000 })
  expect(startCalls).toBe(2)
  expect(pageErrors).toEqual([])
})

test('double-click Begin produces exactly one start request', async ({ page }) => {
  const pageErrors: string[] = []
  page.on('pageerror', (err) => pageErrors.push(err.message))
  await signIn(page)
  await page.goto('/setup')
  let startCalls = 0
  await page.route('**/api/interview', async (route) => {
    const post = route.request().method() === 'POST' ? route.request().postDataJSON() : null
    if (post?.candidate) {
      startCalls += 1
      await new Promise((resolve) => setTimeout(resolve, 600))
    }
    await route.continue()
  })

  await page.getByRole('button', { name: 'Begin interview' }).dblclick()
  await page.waitForURL('**/interview', { timeout: 30_000 })
  expect(startCalls).toBe(1)
  expect(pageErrors).toEqual([])
})
