import { test, expect } from '@playwright/test'
import { attachErrorCollector, hasHorizontalOverflow } from './helpers'

test('landing loads and the primary CTA sends guests to /login', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await page.goto('/')
  await expect(
    page.getByRole('heading', { name: /Prove your skills/i }),
  ).toBeVisible()
  const cta = page.getByRole('link', { name: 'Begin interview' })
  await expect(cta).toHaveAttribute('href', '/setup')
  await cta.click()
  await expect(page).toHaveURL(/\/login/)
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
  expect(errors).toEqual([])
})

test('landing has no horizontal overflow at desktop width', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /Prove your skills/i })).toBeVisible()
  expect(await hasHorizontalOverflow(page)).toBe(false)
})
