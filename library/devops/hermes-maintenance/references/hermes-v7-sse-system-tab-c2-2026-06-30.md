# Hermes V7-SSE — Phase C-2 System-Tab Build-Log (Kompakt-Referenz)

**Datum:** 2026-06-30
**Phase:** C-2 (System-Tab live — Aufbauend auf C-1 Tab-Refactor)
**Quelle:** `~/docs/system/hermes-v7-sse-system-tab-c2-2026-06-30.md` (Full-Version, 4.8 KB)
**Skill-Section:** 11.6 Read-Only System-Monitor-Route-Pattern

---

## Was gebaut wurde

### 3 REST-Endpoints (Express Router, ESM, TypeScript)

| Endpoint | Cache | Datenquelle | Sicherheit |
|----------|-------|-------------|-----------|
| `GET /api/system/health` | 5s | `os.cpus/loadavg/totalmem/freemem` + `fs.statfsSync('/')` + `process.uptime/memoryUsage` | nur Node-Builtins, 0 subprocess |
| `GET /api/system/cron` | 10s | `fs.readFileSync('~/.hermes/cron/jobs.json')` + JSON.parse | read-only fs, KEIN scheduler-trigger |
| `GET /api/system/mnemosyne` | 30s | SQLite read-only via `node:sqlite` (Node 22+) ODER `sqlite3` CLI Fallback | READONLY-mode + fix-pfad + SQL-Escaping |

### Frontend: System-Tab live (dashboard/hermes-sse-dashboard.html)
- 4 KPI-Cards (CPU-Load, RAM-Used, Disk-Used, Mnemosyne-Total)
- 3 Panel-Sektionen in `grid-2`: Host-Health + Cron-Status + Mnemosyne
- Polling 8s, nur wenn Tab aktiv (`state.activeTab === 'system'`)
- 35+ DOM-Marker im HTML
- Vanilla-JS Helpers: `pctClass()`, `setIfExists()`, `ramPctClass()`, `formatMB()`

---

## 3 ESM/TS-Pitfalls die in der Session aufgetreten sind

| # | Pitfall | Fehlermeldung | Fix |
|---|---------|---------------|-----|
| A | `require('node:os')` in ESM-Module | `ReferenceError: require is not defined` | Statische ESM-Imports oben: `import os from 'node:os'` |
| B | `await import(...)` ohne async-Funktion | `TS2308: 'await' expressions are only allowed within async functions` | Function → `async function`, Caller → `await` |
| C | SQLite `ORDER BY 2` mit Concat-Expression | `Error: in prepare, 1st ORDER BY term out of range - should be between 1 and 1` | Sub-Select: `SELECT s\|\|'\|'\|c FROM (SELECT s, c FROM ... ORDER BY c)` |

**Lerneffekt:** ESM-Pitfalls kommen in Clustern — sobald einer gefunden, alle drei nachchecken.

---

## Echte Verifikation (curl roundtrips, kein Mock)

```
=== HEALTH ===
OK | Cores=16 Load=3.42 | RAM=8944MB/15694MB (57%) | Disk=446.54GB/606.99GB (73.6%) | Node=v20.20.2

=== CRON ===
OK | Jobs:10 | Enabled:10 | OK:9 | Err:0 | Pending:1 | DeliveryAlerts:2

=== MNEMOSYNE ===
OK | Total:215 | Working:4 | Episodic:158 | Facts:48 | Scratch:5 | DB:22.87MB
TopSources: [{'source': 'orchestrator-tactical-heuristic', 'count': 3},
             {'source': 'orchestrator-stable-heuristic', 'count': 1}]
TopSessions: [{'session': 'default', 'count': 4}]
```

---

## Phase C Roadmap (nach C-2)

| Phase | Inhalt | Status |
|-------|--------|--------|
| C-1 | Tab-System + Stubs | ✅ |
| **C-2** | System-Health + Cron + Mnemosyne | ✅ (diese Session) |
| C-3 | Meta-Tab (Versions/Config/Docs) + Audit-Log JSONL-Replay | 🟡 bereit |
| C-4 | SSE-Single-Source-of-Truth (kein 2s-Polling) | 🟡 später |
| C-5 | Webhook-Alerts (Canary → Telegram/Slack) | 🟡 später |

---

*Full Version in `~/docs/system/hermes-v7-sse-system-tab-c2-2026-06-30.md`. Querverweis: Skill `devops/hermes-maintenance` Section 11.5 (ESM Pitfalls) + 11.6 (Read-Only Monitor Route Pattern).*
