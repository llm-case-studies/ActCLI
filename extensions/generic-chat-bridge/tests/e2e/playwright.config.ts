import { defineConfig, devices } from '@playwright/test';
import path from 'path';

// Read from env: EXTENSION_PATH, SEMHOST_URL, PLAYGROUND_URL
const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');

export default defineConfig({
  testDir: __dirname,
  timeout: 30_000,
  expect: { timeout: 5_000 },
  reporter: [['list']],
  use: {
    trace: 'retain-on-failure',
    baseURL: process.env.PLAYGROUND_URL || 'http://127.0.0.1:4400',
  },
  projects: [
    {
      name: 'chromium-extension',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          args: [
            `--disable-extensions-except=${EXTENSION_PATH}`,
            `--load-extension=${EXTENSION_PATH}`,
          ],
        },
      },
    },
  ],
});

