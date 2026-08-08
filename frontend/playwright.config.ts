import { defineConfig } from '@playwright/test'
import path from 'node:path'

// E2E topology:
//  - Dedicated deterministic backend on :8001 (LLM disabled), separate from the
//    developer's :8000 instance which may have LLM enabled via backend/.env.
//  - Dedicated Vite dev server on :5174 proxying /api to :8001.
//  - Run against the built preview via PLAYWRIGHT_PREVIEW=1 + PLAYWRIGHT_BASE_URL.
const isPreview = process.env.PLAYWRIGHT_PREVIEW === '1'
const apiPort = process.env.PROBEIQ_E2E_API_PORT ?? '8001'
const frontendUrl = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:5174'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  timeout: 120_000,
  expect: { timeout: 30_000 },
  retries: 0,
  // A single Vite dev server serves all workers; keep parallelism modest so
  // module loads and proxy round-trips stay responsive.
  workers: 4,
  reporter: [['list']],
  use: {
    baseURL: frontendUrl,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    viewport: { width: 1440, height: 900 },
  },
  webServer: isPreview
    ? []
    : [
        {
          command: `uv run uvicorn app.main:app --host 127.0.0.1 --port ${apiPort}`,
          cwd: path.resolve(import.meta.dirname, '..', 'backend'),
          env: {
            ...process.env,
            PROBEIQ_LLM_ENABLED: 'false',
          },
          url: `http://127.0.0.1:${apiPort}/openapi.json`,
          reuseExistingServer: true,
          timeout: 60_000,
        },
        {
          command: 'npm run dev -- --port 5174 --strictPort',
          env: {
            ...process.env,
            PROBEIQ_API_TARGET: `http://localhost:${apiPort}`,
          },
          url: 'http://localhost:5174',
          reuseExistingServer: true,
          timeout: 60_000,
        },
      ],
})
