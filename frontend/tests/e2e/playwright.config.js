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

  globalSetup: './global-setup.js',
  globalTeardown: './global-teardown.js',

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: [
    {
      command: 'npm run start',
      url: 'http://localhost:3000',
      timeout: 300 * 1000,
      reuseExistingServer: true,
      cwd: '../../',
      env: {
        VITE_API_URL: 'http://localhost:8333',
        VITE_USE_MOCK_AUTH: 'true',
        // AuthContext.jsx hard-throws (crashing the whole app) if these are
        // unset — dummy values are fine since Auth0Provider doesn't hit the
        // network until something actually calls login/getAccessTokenSilently.
        VITE_AUTH0_DOMAIN: 'test.auth0.com',
        VITE_AUTH0_CLIENT_ID: 'test-e2e-client-id',
      },
    },
    {
      command: 'venv/bin/python -m uvicorn app.main:app --port 8333',
      port: 8333,
      timeout: 300 * 1000,
      reuseExistingServer: true,
      cwd: '../../../backend',
    },
  ],

  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list'],
  ],
});
