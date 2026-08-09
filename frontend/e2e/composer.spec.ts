import { test, expect } from '@playwright/test'
import {
  attachErrorCollector,
  slowDownAnswers,
  startInterview,
  transcript,
  waitForReply,
  waitForThinking,
} from './helpers'

test('Enter submits the answer and it lands in the transcript', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await slowDownAnswers(page)
  await startInterview(page)
  const textarea = page.getByLabel('Your answer')
  await textarea.fill('Enter submission works')
  await textarea.press('Enter')
  await waitForThinking(page)
  await waitForReply(page)
  await expect(transcript(page)).toContainText('Enter submission works')
  expect(errors).toEqual([])
})

test('Shift+Enter inserts a newline without submitting', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await slowDownAnswers(page)
  await startInterview(page)
  const textarea = page.getByLabel('Your answer')
  await textarea.pressSequentially('line one')
  await textarea.press('Shift+Enter')
  await textarea.pressSequentially('line two')
  await expect(textarea).toHaveValue('line one\nline two')
  await expect(page.getByRole('button', { name: 'Submit' })).toBeEnabled()
  await expect(page.getByRole('status')).toBeHidden()

  await textarea.press('Enter')
  await waitForReply(page)
  await expect(transcript(page)).toContainText('line one\nline two')
  expect(errors).toEqual([])
})

test('empty submission is blocked', async ({ page }) => {
  await startInterview(page)
  const textarea = page.getByLabel('Your answer')
  await textarea.press('Enter')
  await expect(page.getByRole('button', { name: 'Submit' })).toBeDisabled()
  await expect(page.getByRole('status')).toBeHidden()
})

test('4000-character limit is enforced and the counter updates', async ({ page }) => {
  const errors = attachErrorCollector(page)
  await slowDownAnswers(page)
  await startInterview(page)
  const textarea = page.getByLabel('Your answer')
  await textarea.fill('A'.repeat(4000))
  expect((await textarea.inputValue()).length).toBe(4000)
  await expect(page.getByText('4000/4000')).toBeVisible()
  await textarea.press('A')
  expect((await textarea.inputValue()).length).toBe(4000)

  await textarea.press('Enter')
  await waitForReply(page)
  await expect(transcript(page)).toContainText('A'.repeat(64))
  expect(errors).toEqual([])
})
