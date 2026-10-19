import { defineConfig, devices } from '@playwright/test';
import config from './playwright.config.js';

// Render the real app with intercepted APIs; no backend setup or database writes.
export default defineConfig({
  ...config,
  testMatch: '**/ios/post-round-layout.spec.js',
  globalSetup: undefined,
  globalTeardown: undefined,
  retries: 0,
  use: { ...config.use, baseURL: 'http://localhost:3107' },
  projects: [
    { name: 'iphone', use: { ...devices['iPhone 15'] } },
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    ...config.webServer[0],
    command: 'npm run start -- --port 3107 --strictPort',
    url: 'http://localhost:3107',
    reuseExistingServer: false,
  },
});
