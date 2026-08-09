import { test, expect } from '@playwright/test'
import {
  attachErrorCollector,
  signIn,
  slowDownAnswers,
  startInterview,
  submitAnswer,
  waitForReply,
  waitForThinking,
} from './helpers'

test('full journey: one start POST, one POST per turn, all 200, no failures', async ({ page }) => {
  const errors = attachErrorCollector(page)
  const apiStatuses: number[] = []
  const postBodies: unknown[] = []
  const failedRequests: string[] = []
  const nonOk: { url: string; status: number }[] = []

  page.on('response', (res) => {
    if (res.url().includes('/api/interview')) apiStatuses.push(res.status())
    else if (res.status() >= 400 && res.url().startsWith('http://localhost')) {
      nonOk.push({ url: res.url(), status: res.status() })
    }
  })
  page.on('request', (req) => {
    if (req.method() === 'POST' && req.url().includes('/api/interview')) {
      postBodies.push(req.postDataJSON())
    }
  })
  page.on('requestfailed', (req) => failedRequests.push(req.url()))

  await slowDownAnswers(page, 300)
  await startInterview(page)

  const isComplete = () => page.url().includes('/complete')
  let turns = 0
  for (let i = 0; i < 18 && !isComplete(); i++) {
    turns += 1
    await submitAnswer(page)
    await waitForThinking(page)
    await Promise.race([
      waitForReply(page).catch(() => undefined),
      page.waitForURL('**/complete', { timeout: 30_000 }).catch(() => undefined),
    ])
  }
  await expect(page).toHaveURL(/\/complete/, { timeout: 30_000 })

  expect(turns).toBeGreaterThan(0)
  const starts = postBodies.filter((b) => (b as { candidate?: unknown }).candidate)
  const turnsBodies = postBodies.filter((b) => (b as { message?: unknown }).message)
  expect(starts).toHaveLength(1)
  expect(turnsBodies).toHaveLength(turns)
  expect(apiStatuses.every((s) => s === 200)).toBe(true)
  expect(failedRequests).toEqual([])
  expect(nonOk).toEqual([])
  expect(errors).toEqual([])
})

test('landing and setup produce no 4xx/5xx or CORS failures', async ({ page }) => {
  const errors = attachErrorCollector(page)
  const bad: { url: string; status: number }[] = []
  const corsErrors: string[] = []
  page.on('response', (res) => {
    const u = res.url()
    if (!u.startsWith('http://localhost')) return
    if (res.status() >= 400) bad.push({ url: u, status: res.status() })
  })
  page.on('console', (msg) => {
    if (/cors/i.test(msg.text()) && msg.type() === 'error') corsErrors.push(msg.text())
  })

  await signIn(page)
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /Prove your skills/i })).toBeVisible()
  await page.getByRole('link', { name: 'Begin interview' }).click()
  await expect(page.getByLabel('Candidate profile JSON')).toBeVisible()

  expect(bad).toEqual([])
  expect(corsErrors).toEqual([])
  expect(errors).toEqual([])
})
