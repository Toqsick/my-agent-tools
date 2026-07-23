# Hermes V7-SSE Dashboard — Extension Reference (2026-06-30)

> **Companion to:** `hermes-v7-dashboard-build-2026-06-30.md` (Phase A: SSE v2 + Runtime-Store)
> **Covers:** Phase B (Canary + Audit Produktivierung), Phase C-1 (Tab-System), Phase C-2 (System-Tab live)
> **Scope:** Kompakt-Log für schnelles Recall, kein Doc-Mirror

## Phase B — Canary + Audit produktiv

**Ziel:** P2.1 Canary + P1.1 Audit aus hermes-zorin PoC in V7-SSE-Starter portieren.

**Bauen:**
- `src/security/canary.ts` (TypeScript, portiert von PoC `/tmp/hermes-v7/src/security/canary_injector.py`)
- `src/security/audit-log.ts` mit `seedDemoEvents()` für Production-Demo-Population
- `src/api/canary-route.ts` + `src/api/audit-route.ts` (beide mit Zod-Validation)
- `src/observability/event-bus.ts` mit `installCanaryBridge()` + `installAuditBridge()`
- SSE-Event-Typen: `canary.generated`, `canary.alert`, `audit.intent`, `audit.result`

**Endpoints (live verifiziert 2026-06-30):**
- `POST /api/canary/generate` `{ session_id }` → Token-Record
- `POST /api/canary/check` `{ payload }` → { leak: bool, marker? }
- `GET /api/canary` → { totalTokens, totalAlerts, hasActiveRecord, recentTokens, recentAlerts }
- `GET /api/audit` → { total, results, failures, successRate, byTool, topTools, recent }
- `POST /api/audit/clear` (Admin)

**Dashboard:**
- Sidebar: 3 Demo-Buttons (Canary-Generate / Leak-Check / Audit-Clear)
- Security-Panel mit 2 KPI-Cards (Audit-Events, Canary-Tokens), Filter-Pills (Alle/SSE/Security/Audit)
- Live-EventLog mit `canary.alert`-Highlight (rot, level=err)

**Doku:** `~/docs/system/hermes-v7-sse-phase-b-build-2026-06-30.md` (~13.8 KB)

## Phase C-1 — Tab-System statt langer Main-Area

**Schmerz:** Dashboard wuchs auf 6 Sektionen (Hero/KPIs/Lanes/Queue/Audit/Canary/EventLog). User wollte optische Trennung ohne Framework.

**Lösung:** Vanilla-JS-Tabs, Header 3-spaltig (Logo | TabBar | ThemeToggle).

**Trade-offs (ehrlich):**
- ✅ Kein Framework, kein Build-Step
- ✅ localStorage-Persist (`hermes.activeTab`) bleibt nach Browser-Reload
- ✅ Polling-Optimierung spart echte Requests (nicht nur JS-CPU)
- ❌ Tab-Badges nur für Canary (Audit fehlt) — nachrüstbar
- ❌ Keine URL-Hash-Sync (Browser-History ignoriert Tabs)

**Wichtige Code-Patterns (siehe SKILL.md § 11.3 für vollständige Templates):**
```javascript
// Polling-Optimierung
setInterval(() => {
  if (state.activeTab === 'security') { fetchAudit(); fetchCanary(); }
  else if (state.activeTab === 'system') { fetchSystemHealth(); fetchSystemCron(); fetchSystemMnemosyne(); }
}, 8000);  // 8s statt 2s für System-Tab (kein kritischer Live-State)
```

**Doku:** `~/docs/system/hermes-v7-sse-tab-refactor-c1-2026-06-30.md`

## Phase C-2 — System-Tab live

**3 neue Endpoints (alle read-only, gecached):**

| Endpoint | TTL | Datenquelle | Sicherheit |
|----------|-----|-------------|------------|
| `GET /api/system/health` | 5s | `os.cpus/totalmem/freemem/loadavg()` + `fs.statfs('/')` + `process` | Node-Builtins only |
| `GET /api/system/cron` | 10s | `fs.readFileSync('~/.hermes/cron/jobs.json')` + JSON.parse | KEIN Subprocess-Trigger |
| `GET /api/system/mnemosyne` | 30s | `node:sqlite` (Node 22+) oder `sqlite3` CLI Subprocess | DB read-only OR escaped-SQL-Subprocess |

**Verifikations-Curls (echte Messungen, nicht Mock):**
```text
--- /api/system/health ---
{"ok":true,"cpu":{"count":16,"model":"13th Gen Intel(R) Core(TM) i7-13620H","load1":3.42},
 "memory":{"totalMB":15694,"freeMB":6749,"usedPct":57}, "disk":{"totalGB":606.99,"usedPct":73.6}}

--- /api/system/cron ---
OK | Jobs:10 | Enabled:10 | OK:9 | Err:0 | Pending:1 | DeliveryAlerts:2

--- /api/system/mnemosyne ---
OK | Total:215 | Working:4 | Episodic:158 | Facts:48 | Scratch:5 | DB:22.87MB
TopSources: [{'source': 'orchestrator-tactical-heuristic', 'count': 3}, ...]
```

**System-Tab-Frontend:**
- 4 KPI-Cards: CPU-Load, RAM-Used, Disk-Used, Mnemosyne-Total
- `grid-2`: Host-Health (mit progress-bars ok/warn/err) + Cron-Status (10 Jobs mit Status-Icons)
- Mnemosyne: 2-Spalten-Layout (Top-Sources / Persistenz-Counts)
- Polling: 8s, nur wenn `state.activeTab === 'system'`
- CSS: `.sys-metric` `.bar` `.bar-fill.bar-ok|warn|err` `.cron-row` `.mn-row` `.mn-grid`

**Doku:** `~/docs/system/hermes-v7-sse-system-tab-c2-2026-06-30.md`

## Pitfall-Cluster (3 ESM/TS-Stolpersteine)

Vollständig dokumentiert in SKILL.md § 11.5. Hier die **Quick-Referenz-Tabelle**:

| # | Symptom | Ursache | Fix |
|---|---------|---------|-----|
| A | `ReferenceError: require is not defined` | `"type": "module"` blockt CJS | `import os from 'node:os'` am Top |
| B | `TS2308: await expressions only allowed within async functions` | Dynamic `await import('node:sqlite')` | `async function snapshot(): Promise<...>` |
| C | SQLite-CLI: `ORDER BY term out of range - should be between 1 and 1` | Concat-Expression ohne Spalten-Alias | Sub-Select: `SELECT s\|\|'\|'\|c FROM (SELECT ... AS s, ... AS c ORDER BY c)` |

**Diagnose-Tempo:**
1. TSC-Fehler Zeile + Code anschauen
2. Pattern zuordnen (A/B/C)
3. 1-Patch-Fix
4. Bei Phase-C-2-Build waren 4 Patches nötig bevor alles grün war

## Cross-Cuts für spätere Phasen

**Was bewusst NICHT gemacht wurde (out-of-scope Roadmap):**
- C-3: Meta-Tab (Versions/Config/Docs) — Stub existiert (`#panel-meta`)
- C-4: SSE-Single-Source-of-Truth (kein Polling mehr)
- C-5: Webhook-Alerts für Canary nach Telegram/Slack

**Auth-Gap (für Produktion):** Aktuell 0 Auth — alle Routes offen auf 0.0.0.0:4321. `app.use('/api/', generalLimiter)` rate-limited, aber kein Token-Check. **Fix-Skeleton:** Express-Middleware die `X-Hermes-Token`-Header mit `process.env.HERMES_TOKEN` vergleicht.

**Test-Coverage:** 0 .test.ts Files im gesamten Repo. **Test-Sweet-Spot für Erst-Erstellung:** Smoke-Tests pro Endpoint (1 File pro Route, jeder Test < 30 Zeilen). Vitest oder node:test — beides ohne extra Bundler-Setup.

**Mnemosyne-Hygiene Lesson (siehe SKILL.md § 13):**
10 Background-Quittungen (5× Server-Restarts Phase C-2) erzeugten 20 redundante Memories (10× User-Receipt + 10× meine Antwort). Cleanup mit Konsolidierungs-Memo + chain-`invalidate` erledigt. Statt jeder Quittung einzeln zu antworten: kurz bestätigen "sauberes Ende" und im selben Turn ggf. das Memory aufräumen wenn mehrere dazu kommen.

## Quick-Reference Dateipfade

```
Repo:     /home/bratan/Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart/hermes-v7-repo-starter/packages/hermes-sse
Server:   src/server/index.ts
Routes:   src/api/{sse,status,lane,canary,audit,system-health,system-cron,system-mnemosyne}-route.ts
Security: src/security/{canary,audit-log,redact,index}.ts
Obs:      src/observability/event-bus.ts (installCanaryBridge, installAuditBridge)
Midware:  src/middleware/{rate-limiter,schemas,error-handler}.ts
State:    src/state/runtime-store.ts
Dashboard: dashboard/hermes-sse-dashboard.html (1647+ Zeilen, 4 Tabs)
Doku:     ~/docs/system/hermes-v7-sse-*.md
Logs:     ~/.hermes/logs/{canary-tokens,canary-alerts,audit-log}.jsonl
Cron:     ~/.hermes/cron/jobs.json (10 jobs)
Mnemosyne DB: ~/.hermes/mnemosyne/data/mnemosyne.db (22.87 MB)
```

---

*Build-Phase-Reference für Hermes V7-SSE. Wenn du beim Multi-Scout-Auftrag was zum Dashboard gefragt wirst, lies erst diese Reference, dann die SKILL.md § 11.5/11.6.*
