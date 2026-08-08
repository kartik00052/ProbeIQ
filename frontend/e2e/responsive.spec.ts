import { test, expect } from '@playwright/test'
import { attachErrorCollector, hasHorizontalOverflow, startInterview } from './helpers'

const VIEWPORTS = [375, 390, 768, 1024, 1280, 1440]

for (const width of VIEWPORTS) {
  test(`no horizontal overflow at ${width}px`, async ({ page }) => {
    const errors = attachErrorCollector(page)
    await page.setViewportSize({ width, height: 900 })
    await page.goto('/')
    expect(await hasHorizontalOverflow(page)).toBe(false)
    await page.goto('/setup')
    expect(await hasHorizontalOverflow(page)).toBe(false)
    await startInterview(page)
    expect(await hasHorizontalOverflow(page)).toBe(false)
    await expect(page.locator('div.sticky article')).toBeVisible()
    await expect(page.getByLabel('Your answer')).toBeVisible()
    await expect(page.locator('[aria-label="Curriculum coverage"]')).toBeVisible()
    expect(errors).toEqual([])
  })
}
