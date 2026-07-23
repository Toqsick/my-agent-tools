# Live-Data-Provider Pattern for Dashboards

> Session-Reference from Yuno-Dashboard Live-Build (2026-07-01, updated v3)

## Problem

Dashboard-HTML läuft als static file, aber braucht **echte Live-Daten** von Hermes/System.
Direkter `/api/*`-Zugriff ist blockiert (HTTP 401 ohne Auth-Token).

## Lösung: Python Data-Provider + fetch-Polling

### Architektur

```
Browser (live.html)
  ├── fetch() alle 3s → localhost:8767/api/data
  │                          ↑
  │                    server.py (Python HTTPServer)
  │                     ├── urllib → /api/status (no-auth, einziger offener Endpoint)
  │                     ├── subprocess → hermes CLI (skills, profiles, cron)
  │                     ├── psutil → CPU/RAM/Disk/Temp
  │                     └── pathlib → Memory/Session/Cron File-Scans
```

### Hermes API-Surface (evaluiert 2026-07-01)

| Endpoint | Ohne Auth | Mit Bearer Token | Quelle |
|----------|-----------|-----------------|--------|
| `/api/status` | **200 ✓** | 200 | Version, Gateway, Platforms, Sessions |
| `/api/skills` | 401 | 401 (Token aus .env funktioniert nicht) | — |
| `/api/sessions` | 401 | 401 | — |
| `/api/crons` | 401 | 401 | — |
| `/api/profiles` | 401 | 401 | — |
| `/api/health` | 401 | 401 | — |

**Workaround:** `hermes` CLI via `subprocess` nutzen statt API:
```python
result = subprocess.run(
    [f"{HERMES_HOME}/hermes-agent/venv/bin/hermes", "skills", "list"],
    capture_output=True, text=True, timeout=10,
    env={**os.environ, "HERMES_HOME": str(HERMES_HOME)}
)
skill_count = result.stdout.count("enabled")
```

### Caching-Strategie

NICHT bei jedem HTTP-Request alle CLI-Befehle neu ausführen (das dauert 2-5s):

```python
_cache = {}
_cache_ts = {}
CACHE_TTL = 30  # Sekunden

def cached(key, fn, ttl=CACHE_TTL):
    now = time.time()
    if key in _cache and (now - _cache_ts.get(key, 0)) < ttl:
        return _cache[key]
    val = fn()
    _cache[key] = val
    _cache_ts[key] = now
    return val
```

**TTL-Empfehlungen:**
- Skills count: 60s (ändert sich selten)
- Profiles: 60s
- System-Stats (psutil): 0s (immer frisch)
- Hermes-API-Status: 0s (frisch für Gateway-State)
- Session/Cron count: 120s

### Client-Side Polling (3s Refresh — Basti's Präferenz)

```javascript
const DATA_URL = 'http://127.0.0.1:8767/api/data';
const REFRESH_MS = 3000; // 3 Sekunden!

async function fetchData() {
    try {
        const res = await fetch(DATA_URL, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        render(data);
        document.getElementById('error-banner').classList.remove('show');
    } catch (err) {
        document.getElementById('error-banner').classList.add('show');
    }
}

fetchData();
setInterval(fetchData, REFRESH_MS);
```

### Progress-Indicators

**Auto-Refresh Bar** (oben fixiert, füllt sich über ~3s):
```css
.refresh-bar { position: fixed; top: 0; left: 0; height: 2px; background: linear-gradient(90deg, var(--purple), var(--pink)); width: 0; z-index: 9999; transition: width 150ms ease; }
.refresh-bar.active { width: 100%; transition: width 2.8s linear; }
```

```javascript
// Bei jedem fetch: Bar resetten und neu starten
const bar = document.getElementById('refresh-bar');
bar.classList.remove('active');
void bar.offsetWidth; // Reflow-Reset (CRITICAL — ohne das läuft die CSS-Animation nicht neu)
bar.classList.add('active');
```

### Color-Coded Dynamic Bars

```javascript
function colorBar(barId, pct, warn=70, crit=90) {
    const bar = document.getElementById(barId);
    bar.className = 'progress-fill ' + (pct >= crit ? 'error' : pct >= warn ? 'warning' : '');
}
// Grün = ok, Gelb = >70%, Rot = >90%
```

### Start-Skript Pattern

```bash
#!/usr/bin/env bash
# start.sh — startet Data-Provider + HTML-Server + öffnet Browser
python3 server.py > .server-data.log 2>&1 &
python3 -m http.server 8768 --bind 127.0.0.1 > .server-html.log 2>&1 &
xdg-open "http://127.0.0.1:8768/live.html"
```

## Validation

Smoke-Test für Data-Provider:
```bash
# 1. Server erreichbar?
curl -s http://127.0.0.1:8767/health  # → "ok"

# 2. JSON valid?
curl -s http://127.0.0.1:8767/api/data | python3 -c "import sys,json; d=json.load(sys.stdin); print(list(d.keys()))"

# 3. Key fields prüfen
curl -s http://127.0.0.1:8767/api/data | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d['hermes']['version'], 'version missing'
assert d['system']['memory']['percent'] > 0, 'RAM missing'
assert d['skills']['enabled'] > 0, 'skills missing'
print('✓ All fields present')
"
```

## Dependencies

- `psutil` — `pip install psutil` (System-Stats: CPU, RAM, Disk, Temperaturen)
- Python 3.11+ (stdlib `http.server`, `json`, `subprocess`, `pathlib`)
- Hermes CLI erreichbar unter `~/.hermes/hermes-agent/venv/bin/hermes`
- Hermes Dashboard läuft auf Port 9119 (für `/api/status`)

## Common Issues

| Issue | Fix |
|-------|-----|
| `psutil not found` | `pip install psutil --user` |
| CORS-Error im Browser | `Access-Control-Allow-Origin: *` im Response-Header setzen |
| Server startet nicht (Port belegt) | Alte PID-File löschen, `kill` alte Prozesse |
| `/api/status` nicht erreichbar | Hermes Dashboard läuft nicht: `hermes dashboard --port 9119` |
| CLI-Aufrufe zu langsam | TTL-Hochsetzen (60s statt 30s), caching verbessern |
| **Cache-Bug: `_cache_ts[key] = ttl` statt `now`** | **IMMER `_cache_ts[key] = now` — `ttl` ist die TTL-Zahl, kein Timestamp. Symptom: 2-3s Antwortzeit obwohl TTL=60. Diagnose: `_cache_ts`-Werte prüfen (<1000 = Bug aktiv).** |
| `pkill -f "server.py"` signal -15 | Normales SIGTERM, Python HTTPServer fängt das sauber auf. Wenn nicht: `process(action='kill', session_id=...)` nutzen |
| Refresh-Bar läuft nicht neu | `void bar.offsetWidth;` Reflow-Reset zwischen remove+add class ist CRITICAL |

## v3 Lessons (2026-07-01)

1. **3s-Refresh** ist Basti's Präferenz für System-Monitoring — nicht 10s. Die Progress-Bar zeigt dem User "es lebt" ohne zu flackern.
2. **Accordion-Cards** (klickbar, aufklappbar) sind der beste Kompromiss zwischen Übersicht und Detailtiefe — nicht alles auf einmal zeigen.
3. **KPI-as-Buttons** (kleine Cards oben klickbar → öffnen Detail-Card unten mit smooth scroll) ist intuitiver als verschachtelte Menüs.
4. **Mini-Tiles** in aufgeklappten Cards (große Zahlen als Zusammenfassung) geben schnellen Überblick ohne Tabelle lesen zu müssen.
5. **psutil** ist die zuverlässigste Quelle für System-Stats (CPU%, RAM%, Disk%, CPU-Temp, Load-Average) — kein Shell-Parsing nötig.
6. **Nvidia-GPU-Stats via nvidia-smi**: `nvidia-smi --query-gpu=... --format=csv,noheader` gibt Temp, Power, VRAM-Usage, GPU-Util auf einmal. Parse mit `subprocess.run` + `split(', ')`.

## v3.1 Lessons (2026-07-08)

### Mnemosyne Direct Recall in Backend (besser als CLI-Parsing)

Statt `hermes recall` CLI-Output zu parsen (leidet unter Format-Inkonsistenzen), importiere Mnemosyne direkt:

```python
# Im server.py — importiere _handle_recall direkt
from mnemosyne.mcp_tools import _handle_recall

def get_memories(query, top_k=5):
    """Strukturierter Recall mit score/tier/importance/timestamp."""
    try:
        results = _handle_recall(query=query, top_k=top_k)
        # results: [{content, score, tier, time, memory_type, weight_type, topic, importance}]
        return results
    except Exception as e:
        return [{"error": str(e)}]
```

**Vorteile gegenüber CLI:**
- Strukturierte Dicts statt Text-Parsing (Score, Tier, Timestamp separat)
- 5-10x schneller (kein subprocess-Spawn)
- Kein ENV-Home-Auflösungsproblem (import läuft im selben Python-Prozess)

### Subprocess Skill-Run Dispatch (fire-and-forget)

Für Dashboard-Actions wie "Run Skill X" (Quick-Skill-Buttons) muss der Server einen Skill asynchron starten, ohne den HTTP-Request zu blockieren:

```python
import base64
import os

def run_skill_async(name):
    """Startet Hermes-Skill via CLI als daemon. Client kriegt sofort 202 + task_id."""
    task_id = base64.urlsafe_b64encode(os.urandom(6)).decode().rstrip('=')
    subprocess.Popen(
        ["hermes", "skill", "run", f"creative/{name}"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True  # ← CRITICAL: kein Zombie, kein Kill bei Server-Exit
    )
    return task_id
```

**Pitfalls beim Skill-Run im Dashboard-Backend:**

| Problem | Fix |
|---------|-----|
| HTTP-Request hängt bis Skill fertig ist | `Popen` statt `run` — non-blocking |
| Skill-Prozess stirbt wenn Server stirbt | `start_new_session=True` (setsid) |
| Zombie-Prozesse bei vielen Clicks | `close_fds=True` — keine File-Descriptor-Leaks |
| Duplicate skill runs | Task-ID generieren + dedup-Cache (60s TTL) |

### Static-Serving im Data-Provider (vereinfacht Deployment)

Statt zwei getrennten Servern (einer für HTML, einer für API), kann ein server.py **beides** auf einem Port servieren:

```python
# In do_GET:
if self.path in ('/', '/index.html'):
    with open('index.html') as f:
        content = f.read()
    self.send_response(200)
    self.send_header('Content-Type', 'text/html; charset=utf-8')
    self.send_header('Access-Control-Allow-Origin', '*')
    self.end_headers()
    self.wfile.write(content.encode())
```


## v3.2 Lessons (2026-07-08) — Advanced Server Patterns

### Background Poller + History Ring Buffer

Für Live-Dashboards die **Trend-Linien (Sparklines) und History** brauchen, reicht on-request-fetch nicht aus. Der Server muss selbstständig Daten sammeln und in einem Ring-Buffer vorhalten:

```python
import threading
from collections import deque

# Ring Buffer — hält die letzten 60 Datenpunkte (3s × 60 = 3 Minuten)
HISTORY_LENGTH = 60
history_buffer = deque(maxlen=HISTORY_LENGTH)

def background_poller():
    """Läuft in eigenem Thread, snapshottet alle 3s."""
    while True:
        try:
            snap = build_payload_snapshot()  # schnelle Variante ohne CLI (nur psutil + cached CLI)
            history_buffer.append({
                "ts": time.time(),
                "cpu_pct": snap["system"]["cpu_pct"],
                "mem_pct": snap["system"]["memory"]["pct"],
                "gpu_pct": snap.get("system", {}).get("gpu", {}).get("util_pct", 0),
            })
        except Exception:
            pass
        time.sleep(3)

# Start im Hauptthread
poller_thread = threading.Thread(target=background_poller, daemon=True)
poller_thread.start()
```

**Architektur-Trennung:**
- **`build_payload()`** (synchron, on-demand) — ruft alle Datenquellen + CLI-Befehle auf
- **`build_payload_snapshot()`** (lightweight, für Poller) — nur psutil + gecachte CLI-Daten, keine CLI-Aufrufe
- **`/api/history`** — liefert `history_buffer` als JSON-Array

**Behaviour:** Der Poller hält den Cache **warm** (durch Aufruf von `cached()`) und füllt den History-Ring-Buffer.

### SSR (Server-Side Rendering) Snapshot Embedding — 0-Wait Initial Render

**Problem:** Dashboard lädt → Browser zeigt Skeleton/"connecting…" bis der erste async `fetch()` resolved. Bei 2-3s Server-Response (cold) sieht der User 3+ Sekunden leere Karten.

**Lösung:** Server embedet den initialen Daten-Snapshot **inline** in die HTML-Seite als `<script>`-Block:

```python
# In do_GET für index.html:
if self.path in ('/', '/index.html'):
    with open('index.html') as f:
        html = f.read()
    snapshot = json.dumps(build_payload_snapshot())
    ts = int(time.time() * 1000)  # ms für Frontend
    snapshot_inline = f'<script>window.__INITIAL_SNAPSHOT__ = {snapshot}; window.__INITIAL_SNAPSHOT_TS__ = {ts};</script>'
    html = html.replace('</title>', '</title>\n' + snapshot_inline)
    # oder nach <head> einfügen
    html = html.replace('</head>', snapshot_inline + '\n</head>')
    self._send(200, 'text/html', html.encode())
```

**Frontend-Seite (JavaScript):**

```javascript
// SSR Fallback — sofortiger initialer Render ohne fetch
const INIT_SNAPSHOT = (typeof window !== 'undefined' && window.__INITIAL_SNAPSHOT__) || null;

if (INIT_SNAPSHOT) {
  lastData = INIT_SNAPSHOT;
  lastFetchTs = window.__INITIAL_SNAPSHOT_TS__ || Date.now();
  const doSSRRender = () => {
    try {
      renderAll(INIT_SNAPSHOT);
      console.log('[dash] SSR initial render from inline snapshot');
    } catch (e) {
      console.error('[dash] SSR render failed:', e);
    }
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', doSSRRender);
  } else {
    doSSRRender();
  }
}
```

**Vorteil:** Der erste Paint zeigt **echte Daten** statt Skeletons. Der async-Polling-Loop aktualisiert dann im Hintergrund. Nutzer sieht CPU=25% sofort beim Page-Load.

**Wichtig:** `INITIAL_SNAPSHOT` kann groß sein (50-100KB JSON). Zusammen mit dem 80KB+ HTML-Dashboard eine große First-Paint-Load. Perfekt für lokale Dashboards (localhost), nicht empfohlen für Internet-Exposure.

### systemd-User-Service Deployment (Persistenter Hintergrunddienst)

Für Dashboards die **dauerhaft laufen** sollen (nicht nur während der Dev-Session):

```ini
# ~/.config/systemd/user/yuno-dashboard.service
[Unit]
Description=Yuno Dashboard Live Data Provider
After=network.target

[Service]
Type=simple
ExecStart=/home/bratan/.hermes/hermes-agent/venv/bin/python3 /home/bratan/10-Projekte/10-active/yuno-ui/server.py
WorkingDirectory=/home/bratan/10-Projekte/10-active/yuno-ui
Restart=always
RestartSec=5
Environment=HOME=/home/bratan

[Install]
WantedBy=default.target
```

```bash
# Aktivieren:
systemctl --user daemon-reload
systemctl --user enable yuno-dashboard.service
systemctl --user start yuno-dashboard.service

# Status:
systemctl --user status yuno-dashboard.service

# Logs:
journalctl --user -u yuno-dashboard.service -n 50 -f
```

**systemd-Timer für periodische Snapshots (alle 5 Min Telegram):**

```ini
# ~/.config/systemd/user/yuno-dashboard-snapshot.service
[Unit]
Description=Yuno Dashboard Snapshot (Telegram)
[Service]
Type=oneshot
ExecStart=/home/bratan/10-Projekte/10-active/yuno-ui/snapshot-send.py
Environment=HOME=/home/bratan
```

```ini
# ~/.config/systemd/user/yuno-dashboard-snapshot.timer
[Unit]
Description=Dashboard Snapshot alle 5 Minuten
[Timer]
OnCalendar=*:0/5
Persistent=true
[Install]
WantedBy=timers.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable yuno-dashboard-snapshot.timer
systemctl --user start yuno-dashboard-snapshot.timer
```

**Dashboard-Snapshot-Script (`snapshot-send.py`):**

```python
#!/usr/bin/env python3
"""Sammelt Daten von /api/data, erstellt Text-Snapshot, sendet via hermes send."""
import json, subprocess, urllib.request

try:
    r = urllib.request.urlopen("http://127.0.0.1:8767/api/data", timeout=10)
    d = json.loads(r.read())
    msg = (
        f"📊 *Dashboard Snapshot*\n"
        f"CPU: {d['system']['cpu_pct']}% · MEM: {d['system']['memory']['pct']}%\n"
        f"GPU: {d['system'].get('gpu', {}).get('util_pct', '?')}% · Disk: {d['system']['disk']['pct']}%\n"
        f"Skills: {d['skills']['enabled']} · Cron: {d['cron']['active']} jobs"
    )
    subprocess.run(["hermes", "send", "-t", "telegram:7222661188", msg],
                   timeout=30, capture_output=True)
except Exception as e:
    subprocess.run(["hermes", "send", "-t", "telegram:7222661188",
                    f"⚠️ Snapshot failed: {e}"], timeout=30)
```

### hermes-webui Fetch-Proxy Pattern (Offline-Detection)

Inspiriert von `Toqsick/hermes-webui` — der Fetch-Wrapper mit Offline-Erkennung und Auto-Recovery:

```javascript
// Fetch-Patcher — silenced unhandled rejections + Offline-Detection
let _consecutiveErrors = 0;
const OFFLINE_FAILURES_BEFORE_BANNER = 2;
let _offlineVisible = false;

(function patchFetch() {
  if (window.__yunoFetchPatched) return;
  const _orig = window.fetch;
  window.fetch = async function(...args) {
    try {
      const r = await _orig.apply(this, args);
      _consecutiveErrors = 0;
      if (_offlineVisible) {
        _offlineVisible = false;
        console.log('[dash] Back online');
      }
      return r;
    } catch (e) {
      _consecutiveErrors++;
      if (_consecutiveErrors >= OFFLINE_FAILURES_BEFORE_BANNER && !_offlineVisible) {
        _offlineVisible = true;
        console.error('[dash] Server unreachable — offline mode');
        // Optional: Bannner einblenden, Polling pausieren
      }
      throw e;  // nicht schlucken — Caller hat eigenen try/catch
    }
  };
  window.__yunoFetchPatched = true;
})();
```

**Vorteile gegenüber rohem `fetch()`:**
1. **Offline-Banner** wird erst nach N aufeinanderfolgenden Fehlern angezeigt (kein Flackern bei kurzen Netzwerk-Aussetzern)
2. **Auto-Recovery** meldet "Back online" bei erstem Erfolg nach Fehlern
3. Silenced unhandled rejections (keine Chrome-Console-Fehlermeldungen)
4. Caller hat eigenen try/catch — Patcher schluckt nichts
