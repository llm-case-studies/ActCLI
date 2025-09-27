#!/usr/bin/env node
// Seed Zulip with test users and a public stream using Zulip REST API.
// Requires admin API credentials. Obtain API key from the Zulip UI (gear → Personal settings → Your API key).
//
// Usage:
//   ZULIP_SITE=http://127.0.0.1:9991 \
//   ZULIP_EMAIL=admin@local \
//   ZULIP_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \
//   node seed-zulip.mjs

const SITE = process.env.ZULIP_SITE || 'http://127.0.0.1:9991';
const ADMIN_EMAIL = process.env.ZULIP_EMAIL || 'admin@local';
const API_KEY = process.env.ZULIP_API_KEY || '';
const U1_EMAIL = process.env.ZULIP_USER1_EMAIL || 'alice@local';
const U1_PASS = process.env.ZULIP_USER1_PASS || 'alicepass';
const U2_EMAIL = process.env.ZULIP_USER2_EMAIL || 'bob@local';
const U2_PASS = process.env.ZULIP_USER2_PASS || 'bobpass';
const STREAM = process.env.ZULIP_STREAM || 'e2e';

if (!API_KEY) {
  console.error('ZULIP_API_KEY missing. Set ZULIP_EMAIL and ZULIP_API_KEY env vars.');
  process.exit(1);
}

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

function authHeaders() {
  const b64 = Buffer.from(`${ADMIN_EMAIL}:${API_KEY}`).toString('base64');
  return { 'Authorization': `Basic ${b64}`, 'Content-Type': 'application/json' };
}

async function pollReady() {
  for (let i=0;i<60;i++){
    try {
      const r = await fetch(`${SITE}/server_settings`);
      if (r.ok) return true;
    } catch {}
    await sleep(2000);
  }
  throw new Error('Zulip not responding on /server_settings');
}

async function ensureUser(email, password, full_name) {
  // Check if exists by trying to create; if it already exists, Zulip returns error "Email already in use"
  const r = await fetch(`${SITE}/api/v1/users`, {
    method: 'POST', headers: authHeaders(),
    body: JSON.stringify({ email, password, full_name })
  });
  if (r.ok) return;
  const j = await r.json().catch(() => ({}));
  if (j?.msg && /already in use/i.test(j.msg)) return;
  throw new Error(`users create failed: ${r.status} ${j?.msg || ''}`);
}

async function ensureStream(name) {
  // Create and subscribe admin; ignore errors if exists
  const r = await fetch(`${SITE}/api/v1/users/me/subscriptions`, {
    method: 'POST', headers: authHeaders(),
    body: JSON.stringify({ subscriptions: [{ name }], invite_only: false })
  });
  if (r.ok) return;
  const j = await r.json().catch(() => ({}));
  if (j?.msg && (/already exists|already subscribed/i.test(j.msg))) return;
  // Some servers return 400 for duplicate; treat as ok
}

async function subscribeUsers(name, emails) {
  const r = await fetch(`${SITE}/api/v1/users/me/subscriptions`, {
    method: 'POST', headers: authHeaders(),
    body: JSON.stringify({ subscriptions: [{ name }], principals: emails })
  });
  // Non-fatal if some already subscribed
  if (!r.ok) {
    const j = await r.json().catch(() => ({}));
    if (!(j?.msg && /already subscribed/i.test(j.msg))) {
      console.warn('subscribe non-ok:', r.status, j?.msg || '');
    }
  }
}

async function main(){
  console.log('Waiting for Zulip…', SITE);
  await pollReady();
  console.log('Ensuring users…');
  await ensureUser(U1_EMAIL, U1_PASS, 'Alice');
  await ensureUser(U2_EMAIL, U2_PASS, 'Bob');
  console.log('Ensuring stream…');
  await ensureStream(STREAM);
  console.log('Subscribing users to stream…');
  await subscribeUsers(STREAM, [U1_EMAIL, U2_EMAIL]);
  console.log('Done.');
}

main().catch(err => { console.error(err); process.exit(1); });

