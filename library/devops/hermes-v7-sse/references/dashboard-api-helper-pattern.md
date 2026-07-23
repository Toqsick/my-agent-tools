# Dashboard apiFetch + Auth-Helper Pattern

## Was es löst

Browser-Dashboards, die gegen ein auth-required Backend (Express + `X-Hermes-Token`-Header) sprechen, haben zwei Probleme:

1. **EventSource kann keine custom Header setzen** — Token muss in URL als `?token=...`
2. **`fetch('/api/...')` kann zwar Header, aber schickt oft keinen mit** — alle Calls 401en still

Wenn du beides in einem Dashboard mischt (SSE connected, aber `fetchStatus` 401), bleibt die UI auf "Verbundene 0" und "Verbindung fehlgeschlagen" hängen, obwohl die SSE-Layer eigentlich funktionieren. Siehe `hermes-v7-sse` Layer 5 (TDZ) für das noch schlimmere Crash-Pendant.

## Das Pattern (zwei Helper, ein Token-State)

Im `<script>`-Block des Dashboards, **direkt nach den Basis-Helpern** (`$`, `setText`):

```javascript
// === Auth-Helper ZUERST, vor allen fetch-Calls ===
const DEFAULT_AUTH_TOKEN = 'super-secret';
let currentAuthToken = DEFAULT_AUTH_TOKEN;

function apiFetch(path, opts = {}) {
  // 1. Rate-Limit-Cooldown: kurzen Fehler werfen statt Server zu hämmern
  if (Date.now() < rateLimitCooldownUntil) {
    const wait = Math.ceil((rateLimitCooldownUntil - Date.now()) / 1000);
    return Promise.reject(new Error(`rate-limit-cooldown (${wait}s)`));
  }
  // 2. User-Header (z.B. Content-Type) durchlassen, Token IMMER dransetzen
  //    (außer User hat explizit einen anderen X-Hermes-Token)
  const userHeaders = opts.headers || {};
  const headers = {
    ...userHeaders,
    'X-Hermes-Token': userHeaders['X-Hermes-Token'] || currentAuthToken,
  };
  return fetch(path, { ...opts, headers }).then(r => {
    // 3. 429-Cooldown: Retry-After Header respektieren
    if (r.status === 429) {
      const ra = parseInt(r.headers.get('Retry-After') || '30', 10);
      rateLimitCooldownUntil = Date.now() + (ra * 1000);
      console.warn(`[apiFetch] 429 — Cooldown ${ra}s aktiv`);
    }
    return r;
  });
}

let rateLimitCooldownUntil = 0;
```

Dann überall `fetch('/api/...')` → `apiFetch('/api/...')`. Der Token ist **automatisch dran**, der Cooldown **greift vor dem Request**, und der User kann später `currentAuthToken = neuerWert` setzen (z.B. wenn das Frontend einen Login-Dialog bekommt).

## SSE-Connect: gleiche Token-Quelle

Im `connect()` muss derselbe Token in die URL. **Nicht** eine zweite Konstante:

```javascript
function connect() {
  let url = $('sseUrl').value.trim();
  // Token aus currentAuthToken, nicht hardcoded
  if (url && !/[?&]token=/.test(url) && currentAuthToken) {
    url += (url.includes('?') ? '&' : '?') + 'token=' + encodeURIComponent(currentAuthToken);
  }
  const es = new EventSource(url);
  // ...
}
```

So bleibt eine einzige Source-of-Truth. Wenn `currentAuthToken` zur Laufzeit wechselt, kriegt der nächste SSE-Connect automatisch den neuen.

## Sweep-Replace für bestehende Dashboards

Wenn das Dashboard schon 10+ `fetch('/api/...')`-Calls hat, ein einzeiliger Replace-Block:

```bash
python3 << 'EOF'
p = 'dashboard/hermes-sse-dashboard.html'
with open(p) as f:
    c = f.read()
before = c.count("fetch('/api/")
c = c.replace("fetch('/api/", "apiFetch('/api/")
c = c.replace('fetch("/api/', 'apiFetch("/api/')
with open(p, 'w') as f:
    f.write(c)
print(f"Replaced: {before} fetch → apiFetch")
EOF

# Sanity-Checks
grep -c "fetch('/api" dashboard/hermes-sse-dashboard.html   # → 0
grep -c "apiFetch('/api" dashboard/hermes-sse-dashboard.html  # → 16+
```

Dann **Hard-Reload** im Browser — und der DevTools Network-Tab zeigt auf einen Schlag alle Calls mit `X-Hermes-Token` Header. Vorher waren es rote 401s.

## Warum nicht: globales `fetch()`-Override

Manche Frameworks monkey-patchen `window.fetch`. Davon rate ich ab für dieses Pattern, weil:

- User-Code der `fetch()` direkt nutzt kriegt plötzlich Auth-Header, die er nicht erwartet (Privacy)
- Bypässe (z.B. zu einer externen API) werden unintuitiv
- Der Override verschwindet bei Stack-Traces (schwer zu debuggen)

`apiFetch()` ist explizit, auffindbar, und wer es nutzt weiß, dass es authenticated ist. Pattern-Suche `grep "fetch('/api"` zeigt sofort alle Stellen, die umgestellt werden müssen.

## Lessons aus der Session

- **Token-Logik einmal, nicht zweimal**: Wenn sowohl `apiFetch` als auch `connect()` einen Token brauchen, dann aus derselben Variable. Hardcoded `DEFAULT_TOKEN` an zwei Stellen = Drift-Bug.
- **Cooldown vor dem Request, nicht im Catch**: Wenn der Server 429 sagt, ist es zu spät — der nächste Call fliegt schon. Cooldown muss *vor* dem `fetch()` gecheckt werden.
- **Retry-After ist ein Versprechen**: Browser und Server schicken ihn, um dem Client das Warten abzunehmen. Zu ignorieren ist Respektlosigkeit gegenüber dem Rate-Limiter.
- **`headers` spread muss in der richtigen Reihenfolge sein**: `{...userHeaders, 'X-Hermes-Token': ...}` — sonst überschreibt der Default-Token User-Overrides. Pattern: User zuerst, Defaults zuletzt.

## Verwandte Skills

- `hermes-v7-sse` Layer 5 (TDZ) — warum der `<script>`-Block Reihenfolge braucht
- `hermes-v7-sse` Layer 6 (reconnect death-spiral) — wofür der Cooldown da ist
- `vanilla-js-tdz-helper-first` — Helper-First-Pattern für Vanilla-JS-Frontends
