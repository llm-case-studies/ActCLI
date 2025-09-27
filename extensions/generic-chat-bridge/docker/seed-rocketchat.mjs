#!/usr/bin/env node
// Seed Rocket.Chat with test users and a channel using REST API.
// Requires an admin account to already exist (created via UI on first run).
//
// Usage:
//   node seed-rocketchat.mjs [baseUrl]
//   env overrides (see .env.example): RC_ADMIN_EMAIL, RC_ADMIN_PASS, RC_USER1, ...

const BASE = process.argv[2] || process.env.RC_BASE || 'http://127.0.0.1:3000';
const ADMIN_EMAIL = process.env.RC_ADMIN_EMAIL || 'admin@local';
const ADMIN_PASS = process.env.RC_ADMIN_PASS || 'Passw0rd!';
const U1 = process.env.RC_USER1 || 'alice';
const U1_EMAIL = process.env.RC_USER1_EMAIL || 'alice@local';
const U1_PASS = process.env.RC_USER1_PASS || 'alicepass';
const U2 = process.env.RC_USER2 || 'bob';
const U2_EMAIL = process.env.RC_USER2_EMAIL || 'bob@local';
const U2_PASS = process.env.RC_USER2_PASS || 'bobpass';
const CHANNEL = process.env.RC_CHANNEL || 'e2e';

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function pollReady() {
  for (let i=0;i<60;i++){
    try {
      const r = await fetch(`${BASE}/api/info`);
      if (r.ok) return true;
    } catch {}
    await sleep(2000);
  }
  throw new Error('Rocket.Chat not responding on /api/info');
}

async function login(email, password){
  const r = await fetch(`${BASE}/api/v1/login`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ user: email, password })
  });
  if (!r.ok) throw new Error(`login failed: ${r.status}`);
  const j = await r.json();
  if (!j?.data?.authToken) throw new Error('login: missing token');
  return { token: j.data.authToken, userId: j.data.userId };
}

function authHeaders(auth){
  return { 'X-Auth-Token': auth.token, 'X-User-Id': auth.userId, 'content-type': 'application/json' };
}

async function ensureUser(auth, username, email, password){
  // Check if exists
  let exists = false;
  try {
    const r = await fetch(`${BASE}/api/v1/users.info?username=${encodeURIComponent(username)}`, { headers: authHeaders(auth) });
    if (r.ok) exists = true;
  } catch {}
  if (exists) return;
  const r = await fetch(`${BASE}/api/v1/users.create`, {
    method: 'POST', headers: authHeaders(auth),
    body: JSON.stringify({ username, name: username, email, password, verified: true })
  });
  if (!r.ok) throw new Error(`users.create failed: ${r.status}`);
}

async function ensureChannel(auth, name){
  // Try info
  const info = await fetch(`${BASE}/api/v1/channels.info?roomName=${encodeURIComponent(name)}`, { headers: authHeaders(auth) });
  if (info.ok) {
    const j = await info.json();
    return j?.channel?._id;
  }
  const r = await fetch(`${BASE}/api/v1/channels.create`, {
    method: 'POST', headers: authHeaders(auth), body: JSON.stringify({ name })
  });
  if (!r.ok) throw new Error(`channels.create failed: ${r.status}`);
  const j2 = await r.json();
  return j2?.channel?._id;
}

async function invite(auth, roomId, usernames){
  for (const u of usernames){
    await fetch(`${BASE}/api/v1/channels.invite`, {
      method: 'POST', headers: authHeaders(auth),
      body: JSON.stringify({ roomId, user: { username: u } })
    });
  }
}

async function post(auth, roomId, text){
  await fetch(`${BASE}/api/v1/chat.postMessage`, {
    method: 'POST', headers: authHeaders(auth),
    body: JSON.stringify({ roomId, text })
  });
}

async function main(){
  console.log('Waiting for Rocket.Chat…', BASE);
  await pollReady();
  console.log('Logging in as admin…');
  let auth;
  try {
    auth = await login(ADMIN_EMAIL, ADMIN_PASS);
  } catch (e) {
    console.error('Admin login failed. Create admin via UI first, then re-run.');
    throw e;
  }
  console.log('Ensuring users…');
  await ensureUser(auth, U1, U1_EMAIL, U1_PASS);
  await ensureUser(auth, U2, U2_EMAIL, U2_PASS);
  console.log('Ensuring channel…');
  const rid = await ensureChannel(auth, CHANNEL);
  console.log('Inviting users…');
  await invite(auth, rid, [U1, U2]);
  console.log('Posting welcome message…');
  await post(auth, rid, 'Welcome to #'+CHANNEL+' (seeded)');
  console.log('Done.');
}

main().catch(err => { console.error(err); process.exit(1); });

