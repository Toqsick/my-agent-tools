# Hermes V7 Dashboard Build-Index (2026-06-30)

Cross-References für die zwei Hauptphasen der V7-SSE-Dashboard-Bau-Session am 2026-06-30. Jeder Build hatte einen kompletten Build-Report unter `~/docs/system/`. Dieser Index bündelt die Pfade und Lessons so dass eine Wiederaufnahme in einer späteren Session in unter 30 Sekunden Orientierung hat.

## Phase B: Canary + Audit produktivieren + Dashboard erweitern

**Dokumentation:** `~/docs/system/hermes-v7-sse-phase-b-build-2026-06-30.md`

**Was gebaut wurde:**
- `packages/hermes-sse/src/security/{canary,audit-log,index}.ts` — CanaryInjector + AuditLog Klassen, JSONL-Persistenz (`~/.hermes/logs/canary-tokens.jsonl`, `canary-alerts.jsonl`, `audit-log.jsonl`)
- `packages/hermes-sse/src/api/{canary,audit}-route.ts` — Express Router (5 + 3 Endpoints)
- `packages/hermes-sse/src/observability/event-bus.ts` — Bridge: `installCanaryBridge()`, `installAuditBridge()`
- `packages/hermes-sse/src/server/index.ts` — Router-Mount + Bridge-Init beim Startup
- `packages/hermes-sse/dashboard/hermes-sse-dashboard.html` — +260 Zeilen: Security-Panels, Filter-Pills, Demo-Buttons

**Architektur-Entscheidungen:**
1. **Canary-Crypto:** `crypto.randomUUID()` + sha256 → 256-bit Entropie. Token-Set hat 4 Marker pro Token (token_id, fake_api_key, fake_github_token, short_hash).
2. **Singleton-Injector Pattern:** Domain-Modul `canary.ts` exportiert Singleton-Setter. Routes setzen ihn nach `generate()`. Dashboard behält State über Polling alle 2s.
3. **Bridge-Pattern** statt direct emit: Module emittiert auf local EventEmitter, Bridge-Install übersetzt zu SSE-Events. Idempotent (`bridgeInstalled = true`), im `server/index.ts` nach SSE-Init aufgerufen.
4. **JSONL statt SQLite:** Append-only, getrimmt auf 1000 Tokens / 500 Alerts. Trade-off: keine Index-Queries, dafür zero-Migration-Cost.
5. **Audit-Ring-Buffer:** Max 500 in-memory, JSONL-append für Persistenz. Trade-off: process-restart verliert in-memory state; seedDemoEvents() füllt initial.

**Verifikation (E2E live):**
- `npm run check` exit 0, `npm run build` exit 0
- 5 Endpoints antworten 200: `/api/canary`, `/api/canary/generate`, `/api/canary/check`, `/api/audit`, `/api/audit/recent`
- SSE-Stream zeigt `event: canary.generated` + `event: canary.alert` in curl-Capture nach Trigger
- Canary: 6 Tokens / 5 Alerts persistiert nach Test-Runs, Audit: 4 Demo-Events seeded

## Phase C-1: Tab-Refactor (4-Panel-System)

**Dokumentation:** `~/docs/system/hermes-v7-sse-tab-refactor-c1-2026-06-30.md`

**Was gebaut wurde:**
- Dashboard umgebaut von "langer Main-Area" zu Tab-System: 📡 Live / 🛡️ Security / 🧠 System / ℹ️ Meta
- Header als 3-Spalten CSS-Grid (Logo | Tab-Bar mittig | Theme-Toggle)
- Vanilla-JS `setActiveTab()` mit localStorage-Persist
- Polling-Optimierung: Audit/Canary-Polling läuft nur wenn Security-Tab aktiv (spart ~28 req/min)
- Tab-Badges zeigen Canary-Alert-Counter
- System + Meta sind Stubs mit "Coming in C-2/C-3"-Hinweisen + Bullet-Liste geplanter Datenquellen

**Architektur-Entscheidungen:**
1. **Vanilla JS statt React/Vue:** Kein Build-Step, keine Dependencies, lädt schnell. Trade-off: mehr eigene Code-Wartung.
2. **localStorage statt URL-Hash:** Persist über Reload, kein History-API-Setup. Trade-off: nicht shareable per Link.
3. **CSS-only Panel-Switching** mit `display: none/flex`: Simpler als JS-Routing.
4. **Lazy-Load:** `setActiveTab('security')` triggert `fetchAudit()` + `fetchCanary()` für Initial-Load.
5. **Single Event-Log-Container per Tab:** `eventList` (Live) vs `eventListSecurity` (Security) — getrennt um Cross-Tab-Confusion zu vermeiden.

**Verifikation:**
- `npm run check` exit 0, Dashboard 1647 Zeilen, +293 vs Phase-B-Stand
- DOM-Check: 7 `tab-panel`-Vorkommen, 4 `data-tab`-Attribute, 4 Panel-IDs

## Lessons-Crosslinks

- §6 (SSE-Pipeline v2) → Phase B nutzt Production-Pattern unverändert
- §7.2 (Canary-SSE-Bridge-Pattern) → Phase B implementiert exakt dieses Pattern, live verifiziert
- §8.1 (Multi-Task-Mix ohne Priorität) → Bestätigt in dieser Session: 2 Tasks (P2.1 + P1.1) kamen gekoppelt, Ist-Bericht + 4 Optionen-Pattern hat User-Wahl geleitet
- §11.1 (dist/ ist stale nach Rebuild) → Direkt gebraucht: nach Canary-Bridge-Code-Änderung `pkill -f "node dist/server"`, sonst zeigt SSE-Stream alte Bridge-Version
- §11.2 (Vanilla-JS duplizite Funktionen) → Im Phase-C-1 Bug passiert: doppelte `renderEvents()` durch patch-Fehler, Fix via explizites Löschen + neue Definition
- §11.3 (Tab-System Pattern) → Phase-C-1 nutzt exakt dieses Pattern als Vorlage
- §11.4 (IOCTL-Quirk) → Bestätigt in dieser Session: 4+ Background-Curl-Fehlversuche mit Bash-`&`-Pattern

## Status 2026-06-30 End-of-Session

- ✅ Phase B fertig + live verifiziert
- ✅ Phase C-1 fertig
- 🟡 Phase C-2 (System-Tab mit echten Metriken): Ready aber noch nicht angefangen
- 🟡 Phase C-3 (Meta-Tab): Stub
- 🟡 Phase C-4 (SSE-Single-Source-of-Truth statt 2s-Polling): noch Hacky-Hook im Code
- 🟡 Phase C-5 (Webhook-Alerts für Canary): noch nicht angefangen

Main-Branch unangetastet. Build-Stand: `tsc exit 0`, `dist/` frisch, `canary-tokens.jsonl` (6 Einträge), `canary-alerts.jsonl` (5 Einträge). Server startbar auf Port 4321 via `PORT=4321 npm start`.
