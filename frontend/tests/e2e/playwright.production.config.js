import { defineConfig, devices } from '@playwright/test';

/**
 * Production Smoke Test Configuration
 *
 * Runs minimal smoke tests against production URLs to verify deployment.
 * Use: npx playwright test --config tests/e2e/playwright.production.config.js
 */
export default defineConfig({
  testDir: './tests',
  testMatch: '**/smoke-*.spec.js',  // Only run smoke tests
  timeout: 60000,  // 1 minute per test
  retries: 1,
  workers: 1,

  use: {
    baseURL: process.env.FRONTEND_URL || 'https://wolf-goat-pig.vercel.app',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    // Don't wait for network idle - production may have external requests
    actionTimeout: 15000,
  },

  // No local webServer - we're testing production
  webServer: undefined,

  projects: [
    {
      name: 'production-chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  reporter: [
    ['html', { outputFolder: 'playwright-report-production' }],
    ['list'],
  ],
});
