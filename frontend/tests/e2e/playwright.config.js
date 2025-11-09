import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 120000, // 2 minutes per test
  retries: 2,
  workers: 1, // Run serially to avoid port conflicts

  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: [
    {
      command: 'cd ../../backend && uvicorn app.main:app --reload',
      port: 8000,
      timeout: 120000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'cd .. && npm start',
      port: 3000,
      timeout: 120000,
      reuseExistingServer: !process.env.CI,
    },
  ],

  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list'],
  ],
});
