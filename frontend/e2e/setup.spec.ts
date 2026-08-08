import { test, expect } from '@playwright/test'
import { attachErrorCollector } from './helpers'

test('setup loads with the sample profile prefilled and starts the interview', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await page.goto('/setup')
  const textarea = page.getByLabel('Candidate profile JSON')
  await expect(textarea).toBeVisible()
  await expect(textarea).toHaveValue(/member/)
  await page.getByRole('button', { name: 'Begin interview' }).click()
  await page.waitForURL('**/interview')
  await expect(page.locator('div.sticky article')).toBeVisible({ timeout: 30_000 })
  expect(errors).toEqual([])
})

test('invalid JSON shows an inline error and stays on setup', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await page.goto('/setup')
  await page.getByLabel('Candidate profile JSON').fill('{ definitely not valid json')
  await page.getByRole('button', { name: 'Begin interview' }).click()
  await expect(page.locator('.text-danger')).toBeVisible()
  await expect(page).toHaveURL(/\/setup/)
  expect(errors).toEqual([])
})
