# Hermes V7 — Multi-Repo Discovery (2026-06-30)

> **Source:** Live-Discovery beim Working-Task "P2.1 Canary produktivieren + P1.1 Audit-Commit + Dashboard erweitern".
> **Skill:** `hermes-maintenance` Section 7.1 + 7.2 / 8.1.

## TL;DR

Wenn User "Hermes V7 audit-log" oder "canary_injector" fragt: es gibt **drei parallele V7-Varianten** auf der Platte. Erst klären welche die "source of truth" ist, **dann** integrieren.

## Drei Hermes-Varianten (Stand 2026-06-30)

### 1. V7-SSE-Starter (Dashboard-Variante)
**Pfad:** `/home/bratan/Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart/hermes-v7-repo-starter/packages/hermes-sse/`

**Charakteristik:**
- Express + SSE v2 Production-Implementation
- Dashboard `dashboard/hermes-sse-dashboard.html` (888 Zeilen, 34KB)
- Status-Route `src/api/status-route.ts` (liefert runtime-store + SSE-stats)
- KPIS: stream.clients, activeLanes, queueDepth, gateBacklog, leaseConflicts
- **Fehlt:** `audit-log.ts`, `redact.ts`, `canary*` — KEIN Security-Code!

**Vermuteter Zweck:** Production-Grade SSE-Transport für V7 Orchestrator. Dashboard fokussiert auf Runtime.

### 2. Hermes Zorin (ältere Variante)
**Pfad:** `/home/bratan/hermes-zorin/src/security/`

**Charakteristik:**
- Ältere Hermes-Variante, augenscheinlich vor SSE-Pipeline
- Security-Code: `audit-log.ts`, `redact.ts`, `gateway-allowlist.ts`, `egress-guard.ts`, `startup-guard.ts`, `tool-profiles.ts`
- `audit-log.ts` (102 Zeilen): intent+result Log mit Hash-Verknüpfung
- **Hat audit-log!** aber Architektur anders (in-memory `AUDIT_LOG` array, keine Persistenz)

**Vermuteter Zweck:** Pre-Production-Sicherheits-Layer, vor SSE-Architektur-Refactor.

### 3. /tmp/hermes-v7/ — Canary-PoC-Arbeitsverzeichnis
**Pfad:** `/tmp/hermes-v7/src/security/`

**Dateien:**
- `audit-log.ts` (2860 bytes) — Version wie in hermes-zorin
- `canary_injector.py` (7026 bytes) — PoC, getestet mit 2 Demo-Runs
- `egress-guard.ts`, `gateway-allowlist.ts`, `redact.ts`, `startup-guard.ts`, `tool-profiles.ts`, `types.ts`, `index.ts`

**Charakteristik:**
- `canary_injector.py` registriert Tokens in `~/.hermes/logs/canary-tokens.jsonl`
- Alerts werden in `~/.hermes/logs/canary-alerts.jsonl` geloggt
- Doku: `/home/bratan/docs/system/p2-canary-token-poc-demo-2026-06-30.md`
- Doku: `/home/bratan/docs/system/p2-canary-token-research.md` (912 Zeilen, Forschung)

**Vermuteter Zweck:** Working-Copy für P2.1 Canary-Token PoC-Phase. NICHT der finale Ort für Integration.

## Diagnose-Workflow

**Schritt 1 — Existenz-Check (parallel):**
```bash
find /home/bratan/Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart -name "audit-log*" -o -name "canary*" 2>/dev/null
find /home/bratan/hermes-zorin -name "audit-log*" -o -name "canary*" 2>/dev/null
find /tmp -name "audit-log*" -o -name "canary*" 2>/dev/null
```

**Erwartetes Ergebnis (Stand 2026-06-30):**
- V7-SSE-Starter: leer (kein Audit/Canary)
- Hermes Zorin: audit-log.ts (1 Treffer)
- /tmp: audit-log.ts + canary_injector.py (2 Treffer)

**Schritt 2 — User fragen welcher Repo aktiv ist:**
- "Welcher V7-Repo-Pfad ist 'source of truth' für Security-Code?"
- Git-Remote checken: `git -C <repo> remote -v`
- Letzter Commit-Datum vergleichen

**Schritt 3 — Vor Integration:**
- `cp <working-file> <target-repo>/src/security/` mit `git status` danach
- Im V7-SSE-Starter KEIN `src/security/`-Verzeichnis → muss neu angelegt werden
- Bei Canary-Python-in-TypeScript-Repo: TypeScript-Port nötig oder Python-Subprocess-Wrapper

## Lessons Learned

1. **Code in `/tmp/` ist volatile** — überlebt Reboot nicht zuverlässig, ist working-copy, nicht final.
2. **Multi-Repo-Hermes ist nicht durch Git dokumentiert** — kein zentrales Manifest welches Repo "V7.3" ist.
3. **`/tmp/hermes-v7/` paired audit-log.ts + canary_injector.py** — der Canary-PoC braucht das audit-log für Token-Hash-Chain, also sollte man BEIDE zusammen migrieren wenn Integration in echten V7-Repo erfolgt.
4. **V7-SSE-Dashboard zeigt nur Runtime-State** — `/api/status` aggregiert runtime-store, keine externen Datenquellen. Canary-Events + Audit-Events müssen via Event-Bus (`observability/event-bus.ts`) eingeklinkt werden.

## Integration-Pattern wenn Auftrag kommt

Für **P2.1 Canary produktivieren** (in V7-SSE-Starter):

1. `canary_injector.py` → `src/security/canary_injector.ts` portieren (oder Python als sidecar)
2. `audit-log.ts` aus `/tmp/hermes-v7/` → `src/security/audit-log.ts` migrieren
3. `redact.ts`, `egress-guard.ts` ebenfalls migrieren (Dependencies)
4. `event-bus.ts` erweitern: `emitCanaryLeak()`, `emitCanaryGenerated()`
5. `status-route.ts` aggregiert Canary-Counter in Status-Snapshot
6. Dashboard zeigt Canary-Panel: Token-Active-Count + Recent-Leak-Alerts

Für **P1.1 Pre-Exec Audit-Commit** (Tirith-Pattern):

1. `audit-log.ts` registriert `pre_llm_call` Hook via Plugin-System
2. Bei jedem Tool-Call: Intent-Log VOR Ausführung
3. Bei Tool-Result: Result-Log mit `outcome` + `durationMs`
4. Hash-Chain über `inputHash` verknüpft Intent ↔ Result
5. Dashboard zeigt Live-Audit-Stream als neue Event-Kategorie

## Querverweise

- Haupt-Skill: `devops/hermes-maintenance`
  - Section 7: Canary-Token-PoC
  - Section 7.1: Multi-Hermes-Repo-Pitfall (kritisch)
  - Section 7.2: Canary → SSE-Pipeline-Integration Pattern
  - Section 8.1: Multi-Task-Mix ohne Priorität (Ist-Bericht + Optionen)
- Doku: `~/docs/system/p2-canary-token-research.md` (912 Zeilen Forschung)
- Doku: `~/docs/system/p2-canary-token-poc-demo-2026-06-30.md` (PoC-Test-Logs)
- Logs: `~/.hermes/logs/canary-tokens.jsonl`, `~/.hermes/logs/canary-alerts.jsonl`

---

*Discovery von Yuno, 2026-06-30, Session "P2.1 Canary produktivieren + P1.1 Audit-Commit + Dashboard erweitern". Decision pending.*
