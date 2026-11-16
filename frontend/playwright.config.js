import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 45_000,
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:15173',
    browserName: 'chromium',
    launchOptions: process.env.EDUSUB_CHROMIUM_PATH
      ? { executablePath: process.env.EDUSUB_CHROMIUM_PATH }
      : {},
  },
  webServer: [
    {
      command: `${process.env.EDUSUB_PYTHON || 'python'} ../backend/tests/e2e_server.py`,
      url: 'http://127.0.0.1:18000/',
      reuseExistingServer: false,
      timeout: 45_000,
    },
    {
      command: 'npm run dev -- --port 15173 --strictPort',
      url: 'http://127.0.0.1:15173/',
      env: { EDUSUB_E2E: '1' },
      reuseExistingServer: false,
      timeout: 45_000,
    },
  ],
})
