/**
 * Debug credentials loading - see exactly what PW is using
 */

import { test } from '@playwright/test';
import { loadDotEnv } from './env';

const RUN_OSS = process.env.RUN_OSS === '1' || process.env.RUN_OSS === 'true';

test.describe('Credentials Debug', () => {
  test.skip(!RUN_OSS, 'Set RUN_OSS=1 to run credential debug');

  test('show loaded credentials', async () => {
    console.log('🔍 BEFORE loading .env:');
    console.log('RC_USER1:', process.env.RC_USER1 || 'NOT SET');
    console.log('RC_USER1_PASS:', process.env.RC_USER1_PASS ? `[${process.env.RC_USER1_PASS.length} chars] "${process.env.RC_USER1_PASS}"` : 'NOT SET');
    console.log('RC_ADMIN_EMAIL:', process.env.RC_ADMIN_EMAIL || 'NOT SET');
    console.log('RC_ADMIN_PASS:', process.env.RC_ADMIN_PASS ? `[${process.env.RC_ADMIN_PASS.length} chars] "${process.env.RC_ADMIN_PASS}"` : 'NOT SET');

    // Load env
    loadDotEnv();

    console.log('');
    console.log('🔍 AFTER loading .env:');
    console.log('RC_USER1:', process.env.RC_USER1 || 'NOT SET');
    console.log('RC_USER1_PASS:', process.env.RC_USER1_PASS ? `[${process.env.RC_USER1_PASS.length} chars] "${process.env.RC_USER1_PASS}"` : 'NOT SET');
    console.log('RC_ADMIN_EMAIL:', process.env.RC_ADMIN_EMAIL || 'NOT SET');
    console.log('RC_ADMIN_PASS:', process.env.RC_ADMIN_PASS ? `[${process.env.RC_ADMIN_PASS.length} chars] "${process.env.RC_ADMIN_PASS}"` : 'NOT SET');

    // Final values used by test
    const RC_USER = process.env.RC_USER1 || process.env.RC_ADMIN_EMAIL || 'alice';
    const RC_PASS = process.env.RC_USER1_PASS || process.env.RC_ADMIN_PASS || 'alicepass';

    console.log('');
    console.log('🎯 FINAL VALUES THAT WILL BE USED:');
    console.log('Username:', `"${RC_USER}" [${RC_USER.length} chars]`);
    console.log('Password:', `"${RC_PASS}" [${RC_PASS.length} chars]`);

    // Check for whitespace issues
    console.log('');
    console.log('🔬 WHITESPACE ANALYSIS:');
    console.log('Username starts with space:', RC_USER.startsWith(' '));
    console.log('Username ends with space:', RC_USER.endsWith(' '));
    console.log('Password starts with space:', RC_PASS.startsWith(' '));
    console.log('Password ends with space:', RC_PASS.endsWith(' '));
    console.log('Username trimmed:', `"${RC_USER.trim()}"`);
    console.log('Password trimmed:', `"${RC_PASS.trim()}"`);
  });
});