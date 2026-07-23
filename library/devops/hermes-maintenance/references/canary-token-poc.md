# Canary-Token-PoC & Multi-Repo Discovery (Full Details)

> Extracted from hermes-maintenance SKILL.md Sections 7, 7.1, 7.2. Canary token implementation, multi-Hermes-repo pitfalls, and SSE-pipeline integration patterns.

## Canary-Token Overview

Canary-Tokens sind synthetische Marker im System-Prompt die bei Auftauchen in Output/Traffic Datenleck beweisen. **Zero-False-Positives** weil Token keinen legitimen Grund hat im Traffic zu landen.

**Best-Practice-Token:**
- Format: `CANARY-<16hex>-<session_hash>`
- Mindestlänge 16+ Zeichen
- Pro Session einzigartig (uuid4 + sha256)
- Pro Token-Set 4 Marker: `token_id`, `fake_api_key`, `fake_github_token`, `short_hash` (für schnelle Pattern-Matches)
- Registry in `~/.hermes/logs/canary-tokens.jsonl` (append-only)
- Alerts in `~/.hermes/logs/canary-alerts.jsonl` (JSONL, mit timestamp, severity, traffic_snippet)

**PoC-Pattern:** Kann mit nur `secrets` + `uuid` + `hashlib` (alle stdlib) gebaut werden. Kein externer Service nötig (kein canarytokens.org dependency).

**Pyright-Hardening:** `datetime.utcnow()` ist deprecated → `datetime.now(timezone.utc)`. LSP-Diagnostics melden das, Runtime läuft trotzdem. Fix vor Production.

## Multi-Hermes-Repo-Pitfall (kritisch — 2026-06-30)

**Symptom:** User fragt nach "Hermes V7 audit-log" oder "canary_injector" — `find` zeigt 0-3 Treffer in unterschiedlichsten Pfaden, du weißt nicht welcher der "echte" ist.

**Reality (Stand 2026-06-30):** Es existieren DREI Hermes-V7-Varianten parallel auf der Platte:

| Pfad | Variante | Enthält |
|---|---|---|
| `/home/bratan/Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart/hermes-v7-repo-starter/packages/hermes-sse/` | **V7-SSE-Starter** (Dashboard-Variante) | `src/api/sse-server-v2.ts`, `src/state/runtime-store.ts`, `dashboard/hermes-sse-dashboard.html` — **KEIN audit-log, KEIN canary** |
| `/home/bratan/hermes-zorin/src/security/` | **Hermes Zorin** (ältere Variante) | `audit-log.ts`, `redact.ts`, `gateway-allowlist.ts`, `egress-guard.ts`, `startup-guard.ts`, `tool-profiles.ts` |
| `/tmp/hermes-v7/src/security/` | **Canary-PoC-Arbeitsverzeichnis** | `canary_injector.py` (paired mit `audit-log.ts`) |

**Diagnose-Workflow wenn User nach Security-Code fragt:**
```bash
# 1. Beide bekannten Standorte parallel checken
find /home/bratan/Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart -name "audit-log*" 2>/dev/null
find /home/bratan/hermes-zorin -name "audit-log*" 2>/dev/null
find /tmp -name "audit-log*" 2>/dev/null

# 2. Wenn Treffer in /tmp → das ist meistens die Working-Copy,
#    der "echte" Repo-Pfad hat dann KEINEN audit-log
# 3. User IMMER fragen welcher Repo "source of truth" ist, BEVOR du integrierst
```

**Pitfall:** Nicht blind in einen Pfad integrieren — wenn Code in `/tmp/hermes-v7/` liegt aber der "echte" V7-Repo woanders ist, brichst du bei jedem `git pull` und verlierst die Integration.

**Lesson (2026-06-30):** Bei Security-Code-Integration in Hermes IMMER erst klären welcher Repo-Pfad aktiv ist (per `git remote -v` + `ls`). Sonst landet Canary-Injector in `/tmp/` statt im echten Repo und Dashboard-Updates sehen den Code nicht.

## Canary → SSE-Pipeline-Integration Pattern (PROVEN — 2026-06-30)

**Architektur-Entscheidung:** Canary-Alerts UND Audit-Intents/Results werden als SSE-Event emittiert, nicht nur in JSONL loggen. Vorteil: Dashboard zeigt Leak-Status live, kein extra Polling-Endpoint nötig.

**Bewährtes Pattern (TypeScript-Implementation, live verifiziert 2026-06-30 in Phase-B-Build):**

```typescript
// 1. In security/canary.ts: domain-local EventEmitter
import { EventEmitter } from 'node:events';
export const canaryEvents = new EventEmitter();
export const auditEvents = new EventEmitter();

// Generator (in der Klasse):
canaryEvents.emit('canary.generated', this.record);
canaryEvents.emit('canary.alert', alert);

// 2. In observability/event-bus.ts: Bridge-Installer (einmalig beim Server-Start)
let bridgeInstalled = false;
export function installCanaryBridge(): void {
  if (bridgeInstalled) return;
  bridgeInstalled = true;
  canaryEvents.on('canary.generated', (record) => {
    emitHermesEvent({ type: 'canary.generated', message: `🔐 ${record.token_id} ...`, scope: 'security / canary', level: 'ok' });
  });
  canaryEvents.on('canary.alert', (alert) => {
    emitHermesEvent({ type: 'canary.alert', message: `🚨 LEAK: ${alert.matched_marker} ...`, scope: 'security / canary', level: 'err' });
  });
}

// 3. In server/index.ts: einmaliger Install beim Startup (nach SSE-Init)
installCanaryBridge();
installAuditBridge();
seedDemoEvents();
```

**Wichtig — Reihenfolge der Bridge-Installation:**
1. SSE-Backend initialisieren (`broadcastSSEv2` muss verfügbar sein)
2. Bridge-Installer aufrufen (lauscht auf domain-Events)
3. NICHT vor Bridge-Install Events emittieren (gehen verloren)

**Vorteile gegenüber Polling:**
- Latency ≤ 1s statt 5-30s Polling-Intervall
- Dashboard zeigt Leak SOFORT (UX-Alert-Toast, roter Border)
- Audit-Trail lückenlos (kein "wir hatten polling gerade aus")
- Single-Source-of-Truth auf Backend-Seite (EventEmitter), Frontend kann via SSE + Polling beide Datenpfade nutzen

**Vollständige Implementation:**
- Security-Module: `packages/hermes-sse/src/security/{canary,audit-log,index}.ts`
- Routes: `packages/hermes-sse/src/api/{canary,audit}-route.ts`
- Bridge: `packages/hermes-sse/src/observability/event-bus.ts` (`installCanaryBridge`, `installAuditBridge`)
- Build-Report: `~/docs/system/hermes-v7-sse-phase-b-build-2026-06-30.md`
