// Minimal EventSource client with all four SSE-frontend patterns baked in.
// Drop this into a vanilla HTML dashboard and adapt `currentAuthToken` +
// `apiFetch` calls to your own backend.

// ----- 1. Auth token (single source of truth) -----
const DEFAULT_AUTH_TOKEN = 'super-secret';
let currentAuthToken = DEFAULT_AUTH_TOKEN;

// ----- 2. apiFetch wrapper: 429-cooldown + token header -----
let rateLimitCooldownUntil = 0;
function apiFetch(path, opts = {}) {
  if (Date.now() < rateLimitCooldownUntil) {
    const wait = Math.ceil((rateLimitCooldownUntil - Date.now()) / 1000);
    return Promise.reject(new Error(`rate-limit-cooldown (${wait}s)`));
  }
  const userHeaders = opts.headers || {};
  const headers = {
    ...userHeaders,                                       // user headers FIRST
    'X-Auth-Token': userHeaders['X-Auth-Token'] || currentAuthToken,
  };
  return fetch(path, { ...opts, headers }).then(r => {
    if (r.status === 429) {
      const ra = parseInt(r.headers.get('Retry-After') || '30', 10);
      rateLimitCooldownUntil = Date.now() + (ra * 1000);
      console.warn(`[apiFetch] 429 — Cooldown ${ra}s aktiv`);
    }
    return r;
  });
}

// ----- 3. SSE connect with exponential-backoff auto-reconnect -----
let sseConn = null;
let sseReconnectAttempt = 0;
let sseReconnectTimer = null;

function connectSSE(basePath = '/api/events') {
  if (sseConn) { sseConn.close(); sseConn = null; }
  const url = basePath + (basePath.includes('?') ? '&' : '?')
    + 'token=' + encodeURIComponent(currentAuthToken);
  console.log('[SSE] Connecting to:', url);
  try {
    sseConn = new EventSource(url);
  } catch (err) {
    console.error('[SSE] THROW:', err);
    return;
  }

  sseConn.onopen = () => {
    sseReconnectAttempt = 0;
    if (sseReconnectTimer) { clearTimeout(sseReconnectTimer); sseReconnectTimer = null; }
    console.log('[SSE] OPEN ✓');
    onSSEOpen && onSSEOpen();
  };
  sseConn.onmessage = (msg) => {
    let payload;
    try { payload = JSON.parse(msg.data); } catch { payload = { type: 'message', message: msg.data }; }
    onSSEMessage && onSSEMessage(payload);
  };
  sseConn.onerror = (e) => {
    console.error('[SSE] ERROR:', { readyState: sseConn.readyState, status: sseConn.status, url: sseConn.url });
    if (sseConn.readyState === EventSource.CLOSED) {
      sseReconnectAttempt++;
      const delay = Math.min(60000, 2000 * Math.pow(2, sseReconnectAttempt - 1));
      if (sseReconnectTimer) clearTimeout(sseReconnectTimer);
      sseReconnectTimer = setTimeout(() => {
        if (!sseConn || sseConn.readyState === EventSource.CLOSED) connectSSE(basePath);
      }, delay);
    }
    // readyState === CONNECTING: browser is already retrying, do NOT double up
  };
}

function disconnectSSE() {
  if (sseReconnectTimer) { clearTimeout(sseReconnectTimer); sseReconnectTimer = null; }
  if (sseConn) { sseConn.close(); sseConn = null; }
}

// ----- 4. Override these handlers in your app -----
let onSSEOpen = null;
let onSSEMessage = null;

// ----- Example wiring -----
// onSSEOpen = () => { document.body.classList.add('connected'); };
// onSSEMessage = (event) => { console.log('event:', event); };
// connectSSE('/api/events');

// ----- Helper: quiet fetchStatus (no spam on 429) -----
async function fetchStatus(path) {
  try {
    const r = await apiFetch(path);
    if (!r.ok) throw new Error('status ' + r.status);
    return await r.json();
  } catch (err) {
    if (err.message.startsWith('rate-limit-cooldown')) return null;
    console.error('Status-Fetch fehlgeschlagen:', err);
    return null;
  }
}
