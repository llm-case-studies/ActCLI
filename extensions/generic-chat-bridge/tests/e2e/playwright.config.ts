import { defineConfig, devices } from '@playwright/test';
import path from 'path';

// Read from env: EXTENSION_PATH, SEMHOST_URL, PLAYGROUND_URL
const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');

export default defineConfig({
  testDir: __dirname,
  workers: 1,
  timeout: 30_000,
  expect: { timeout: 5_000 },
  reporter: [['list']],
  use: {
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    // Use server root; tests will resolve /playground pages explicitly.
    baseURL: process.env.PLAYGROUND_URL || 'http://127.0.0.1:4400',
  },
  projects: [
    {
      name: 'chromium-extension',
      use: {
        ...devices['Desktop Chrome'],
        headless: false,
        viewport: { width: 1700, height: 1100 },
        launchOptions: {
          args: [
            `--disable-extensions-except=${EXTENSION_PATH}`,
            `--load-extension=${EXTENSION_PATH}`,
            `--window-size=1700,1100`,
          ],
        },
      },
    },
  ],
});
