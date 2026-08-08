import { test, expect } from '@playwright/test'

test('WebGL presence canvas mounts on capable hardware', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('canvas')).toHaveCount(1, { timeout: 20_000 })
})

test('no-WebGL falls back to a static poster without a canvas', async ({ browser }) => {
  const context = await browser.newContext()
  await context.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext.bind(HTMLCanvasElement.prototype)
    HTMLCanvasElement.prototype.getContext = function (
      this: HTMLCanvasElement,
      type: string,
      ...args: unknown[]
    ) {
      if (type === 'webgl' || type === 'webgl2') return null
      return original.call(this, type, ...args)
    }
  })
  const page = await context.newPage()
  await page.goto('/')
  await expect(page.locator('canvas')).toHaveCount(0)
  await expect(page.getByRole('heading', { name: /Prove your skills/i })).toBeVisible()
  await context.close()
})

test('low-power device uses the static presence fallback', async ({ browser }) => {
  const context = await browser.newContext({ hasTouch: true })
  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'hardwareConcurrency', { configurable: true, get: () => 2 })
    try {
      Object.defineProperty(navigator, 'deviceMemory', { configurable: true, get: () => 2 })
    } catch {
      // non-configurable in some builds; the CPU check still applies
    }
  })
  const page = await context.newPage()
  await page.goto('/')
  await expect(page.locator('canvas')).toHaveCount(0)
  await context.close()
})
