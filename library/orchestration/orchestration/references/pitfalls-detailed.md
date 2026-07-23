# Pitfalls — Detailed (20 Common Failure Modes)

Full descriptions of all 20 multi-agent pitfalls with context, examples, and remediation steps.
Loaded from `multi-agent-orchestration` SKILL.md §"Pitfalls".

For symptom-based quick reference (top-20 trigger-watchlist), load the companion skill `multi-agent-pitfalls-cheatsheet`.

---

## Pitfall 1: CLI syntax assumed, not checked

Subagents run `hermes config set <made-up-key>` or `hermes tools --foo` without `--help`-checking. The command silently succeeds in some configs and fails in others.

**Fix:** Always `--help` first when introducing a CLI command. If a subagent reports a key like `tool.parallel_calls`, verify it exists: `grep -n "<key>" ~/.hermes/hermes-agent/cli-config.yaml.example`. Empty = confabulated.

## Pitfall 2: Timeouts too short

`timeout=60` for `npm install` or `pip install` regularly fails. Build/install commands need 60-120s+ depending on network.

**Fix:** Set timeout based on the operation. Network-bound: 120s. Local pip: 60s. Heavy `apt install`: 300s. Web fetches: 30s.

## Pitfall 3: Experts without shell access → estimates not measurements

A subagent briefed only with `web, search` will write claims like "service is running" without proof. The whole point of multi-agent is measurement.

**Fix:** Always include `terminal` + `file` toolsets for system-analysis experts. Web-only is acceptable for pure research tasks.

## Pitfall 4: "5 min" estimates are optimistic

Subagents underestimate based on naive path-count. Real: dependency-resolution, network latency, retries.

**Fix:** In the briefing, include "Pre-Check" step: `which <tool>` / `dpkg -l | grep <pkg>` / `npm ls <pkg>`. If absent, scale up time estimate.

## Pitfall 5: Subagent self-reports are NOT facts

"✅ fixed" / "✅ done" in a subagent summary is a CLAIM, not verified state. Pitfall #9 ("write-denied" + "claims done") and Pitfall #11 ("YAML corrupted but reported OK") are sub-cases.

**Fix:** For every "fixed" claim, parent runs `read_file` / `terminal` / `hermes config get` to confirm. Pitfall #29: file may not even exist on disk. **Trust nothing.**

## Pitfall 6: Explicit output paths prevent file chaos

Subagents left to default output paths write to `~/.hermes/skills/` (breaks the skill tree), `/tmp/` (gets cleaned), or current dir (hard to find later).

**Fix:** Always specify `OUTPUT: ~/docs/system/NAME-YYYY-MM-DD.md` in every expert briefing. Never trust defaults.

## Pitfall 7: Config files block subagent writes

Subagents in `--approval required` mode get blocked on every `config.yaml` / `.env` write. They then report "blocked" but parent assumes they fixed it.

**Fix:** Parent collects all YAML/env changes from subagent reports and applies centrally. Never let multiple subagents touch the same config in parallel (Pitfall #11).

## Pitfall 8: YAML config manipulation belongs in parent

Subagents do not have visibility into the full config schema. They invent keys that don't exist. Even when they apply changes, they often break formatting (indentation, anchors, list-vs-scalar).

**Fix:** Subagent outputs a "proposed diff" in their report. Parent reviews and applies with `hermes config set` or Python `yaml.dump` (with backup first).

## Pitfall 9: Web-API subagents hang on slow endpoints

OpenRouter / HuggingFace / GitHub APIs can hang on first call. Subagent burns all 8 web-call budget on one slow endpoint.

**Fix:** Set explicit `MAX 8 web-calls. After 8 -> synthesis with what you have` in every web-heavy briefing. Pair with `OUTPUT-LIMITS` for log files.

## Pitfall 10: `model` param in delegate_task is silently IGNORED

The `model` parameter is documented but ignored. Subagent runs on system default regardless of what you pass.

**Fix:** The only way to control subagent model is `delegation.model` in `~/.hermes/config.yaml` (async) or `skill_lanes.registry` profiles. For ACP-compatible CLIs, use `acp_command` instead.

## Pitfall 11: Delegate-Gate-Blocker

Wenn `delegate_task` mit `base_prompt is empty; nothing to dispatch`, Provider-Gate-Fehlern oder Provider-HTTP-Fehlern wie OpenRouter 404 scheitert, nicht endlos retryen. Parent übernimmt die 3 Expert-Scopes direkt, schreibt verifizierbare Reports und dokumentiert den Fallback.

**Fix:** Parent-direct fallback: run the same 3 expert scopes with terminal/file/web measurements, write reports to explicit paths, synthesize in `~/docs/system/`, state fallback was used.

## Pitfall 12: Free-model rate limits

20 req/min, 200/day on most free tiers. After 3-5 retries with HTTP 429, subagent is dead in the water.

**Fix:** Subagent summaries are leads, not facts. Verify critical claims with direct terminal/file inspection. Complete high-confidence fixes directly. Keep subagent scopes narrow (8-12 concrete questions max).

## Pitfall 13: Silent Truncation von Depp-Modellen

Ein Depp-Worker (Niedrigvertrauens-Modell, z.B. `openrouter/owl-alpha`) kann ein strukturell valides, scheinbar vollständiges Output-Artefakt liefern, das intern still abgeschnitten wurde (Token-Limit erreicht, kein Fehlercode, korrekte JSON-Hülle, inkomplette Nutzlast). Propagiert ungeprüft in die nächste Stage → höherwertiges Modell baut mit hoher Konfidenz auf fehlerhaften Daten auf.

**Gegenmaßnahmen:**
- (a) Stage-Gate-Contract mit Sentinel-Token (`##DEPPS_DONE##`) zwischen Worker und Validator.
- (b) Validation-Phase zwischen Depp-Worker-Output und Queen-Stage: prüfe Sentinel vorhanden? Struktur valide (json.loads/ast.parse)? Längen-Anomalie (< 30% Median)? API-Response `finish_reason == "length"`?
- (c) Bei Truncation-Verdacht: NICHT denselben Prompt retryen — Scope halbieren, oder strukturellen Task anders chunken.
- (d) Audit-Log muss unterscheiden zwischen echtem Depp-Fehler (API 4xx/5xx), Silent Truncation (Sentinel/Struktur/Länge), und intentional kurzem Output (Sentinel da, Struktur ok, Finish `stop`) — drei verschiedene Actions.

Vollständiges Design: siehe `depps-orchestration` Skill (Skeleton, Implementierung steht aus).

## Pitfall 14: Cron-Skripte können Config-Switches still überschreiben

Wenn du manuell `model.provider` oder `delegation.provider` in `~/.hermes/config.yaml` änderst, prüfe VORHER ob ein Cron-Skript (z.B. `hermes-network-monitor` ruft `~/.hermes/scripts/hermes-network-switch.sh` alle 15 Min) hardcoded `DESIRED_PROVIDER`/`DESIRED_MODEL`-Variablen hat. Solche Skripte überschreiben deinen Switch binnen Minuten ohne Warnung.

**Workflow bei Provider-Switch:**
- (a) `grep -rn "DESIRED_PROVIDER\|provider.*openrouter\|provider.*ollama" ~/.hermes/scripts/*.sh` BEVOR du Config patchst.
- (b) Wenn gefunden: Skript selbst mit-patchen (sonst zerstört der nächste Cron-Lauf deine Arbeit).
- (c) Nach Fix: manueller Test `bash ~/.hermes/scripts/<switch-script>.sh` → muss "Bereits auf <neuer-provider>" ausgeben.
- (d) Backup anlegen BEVOR: `cp <script> <script>.bak.$(date +%Y%m%d_%H%M%S)`.

Dokumentiert in Session 2026-06-29 (siehe `~/docs/system/2026-06-29-session-telegram-disk-openrouter.md`).

## Pitfall 15: GitHub MCP Docker-Wrapper Token-Sync

Wenn der konfigurierte GitHub-MCP-Server (z.B. via `docker run toqsick/github-mcp-server:develop`) mit Token=`DEIN_NEUER_TOKEN` (Platzhalter) oder einem abgelaufenen Token läuft, liefert jeder MCP-Aufruf `401 Bad credentials`.

**Symptom:** `GET https://api.github.com/user → 401` trotz vermeintlich korrekter Auth in `config.yaml`.

**Ursachen:** (a) Token-Platzhalter nie ersetzt, (b) `.env` überschreibt `config.yaml` (check BOTH), (c) Token abgelaufen, (d) Docker-Container cached alten Token.

**Workaround (schneller als Token-Fix):** `gh` CLI statt MCP-Wrapper. gh nutzt Keyring-Authentifizierung (`~/.config/gh/hosts.yml`), ist robust gegen Token-Sync-Probleme.

**Workflow:**
- (a) `gh auth status` — wenn logged in: nutze gh für alle GitHub-Operations.
- (b) `gh issue create --title "..." --body "..." --label "..." --assignee "..."` für Issue-Erstellung.
- (c) `git checkout -b feature/...` + `git commit` + `git push -u origin feature/...` für Branch-Push.
- (d) Token-Fix im MCP-Config nachholen (für künftige Sessions).

Dokumentiert in Session 2026-06-29 (Lane 4 der Hermes-V7.1-Mission: `Toqsick/hermes-v7/issues/5` per `gh issue create` erstellt).

## Pitfall 16: Queen-Lane-Plan Pattern für strukturierte Multi-Lane-Missionen

Wenn der User eine Mission mit expliziten Lanes, Gate-Reviews und Übergabepunkten definiert (typisches Pattern: "Lane 1 Research → Lane 2 Matrix → Lane 3 Architektur → Gate-Review → Lane 4 Implementation"), NICHT sofort alle Lanes parallel an Subagenten feuern. Stattdessen:

- (a) Queen-Direct-Plan-Artefakt mit Zeitbudget+Success-Criteria+Blocker zuerst.
- (b) Inventory-Check-First BEVOR Plan final (Realität kann Scope radikal ändern).
- (c) Mechanische Tasks selbst mit `execute_code` (Python-Bulk-Analysis), Reasoning-Tasks an Subagenten.
- (d) Deterministischer Critic für Gate-Review (PASS/FAIL mit JSON-Output), BEIDE Reviewer müssen grün.
- (e) Lane 4 produziert verifizierbare Handles (Issue-URL, Branch-Name), Queen verifiziert sie selbst.
- (f) Retrospektiv-Artefakt am Ende.

Speedup-Beweis: 11 Lanes in 72min vs 390min geplant = **5.4x**. Vollständiges Pattern: siehe `hermes-orchestration` (V2.5+) → `Queen-Lane-Plan Pattern`.

## Pitfall 17: Parent-Direct statt Subagent-Dispatch für eng umrissene Bau-Tasks

Wenn die User-Anfrage **eng umrissene Lanes** mit klaren Code-Pfaden vorgibt (z.B. "bau 3 Meta-Endpoints für X-Pattern wie ich es schon getan hab"), NICHT 3 Subagenten parallel anwerfen, sondern Parent-Direct-Execution mit structured Lane-Plan. (PROVEN 2026-06-30, C-3+C-4 Sprint)

**Begründung:**
- Subagents haben eigenen Context → sehen nicht die aktuelle Repository-Realität (Imports, schon vorhandene Helper, exakte Patterns)
- Parent kennt die Codebase bereits aus Vorrunden → eine Lane dauert 15-20min Parent-Direct, würde mit Subagent-Kontext-Burn 2-3× dauern
- Verifikations-Quality ist **immer besser** mit Parent-Direct: jeder Fix kann sofort via `grep`/curl re-verified werden statt "Self-Report" zu glauben

**Trigger-Frage:** Wenn die Lanes <30min Aufwand sind UND im Repo-Baum bleiben, fahr Parent-Direct mit `Queen-Lane-Plan`-Inventur. Subagent-Dispatch lohnt sich nur für Research/Exploration über mehrere Domains.

**Referenz:** C-3+C-4 Hermes-V7-SSE Sprint 2026-06-30 — 6 Lanes, 110min Queen-Direct, alle 18/18 Tests grün. Mit Subagenten hätte der gleiche Sprint vermutlich 3h+ gedauert wegen Context-Reinjection-Overhead.

## Pitfall 18: Phase-0-Inventur als explizite Phase vor Plan

Queen-Lane-Plan mit explizitem "Inventur-Check" als **Phase 0** (vor Phase 1 der ersten Lane). Gründe: Realität schlägt Plan, und Inventur verhindert Halluzinations. (PROVEN 2026-06-30)

- **Was existiert schon?** `grep -rn "pattern" /src/` → vorhandene Helper, schon verkabelte Events, schon vorhandene Routes
- **Wo sind die harten Daten her?** Welche JSONL-Files existieren, welche Cron-Jobs haben schon Output
- **Welche Patterns sind im Repo?** Convention checken (`require` vs `import`, Error-Format, Naming)
- **Welche Tests/Refs schon da?** Verhindert Re-Discovery

Inventur mit 3-5 parallelen terminal-Calls = 30-60sec. Spart 30min falsches Planen.

## Pitfall 19: ESM/TS-Import-Bug Pattern bei Hermes-v7 Code

In Hermes-v7 `packages/hermes-sse/src/` ist `"type": "module"` + TypeScript-`esModuleInterop:true` Setup. Drei Stolpersteine die mehrfach 2-3 Iterationen gekostet haben:

- **`require(...)` wirft ReferenceError im Runtime-Build**, auch wenn `tsc` kompiliert. Im Source `import x from 'y'` statt `const x = require('y') as ...`. Symptom: `ReferenceError: require is not defined` in `node dist/...`.
- **`await` braucht `async`-Context** — dynamische `await import('node:sqlite')` als Top-Level in non-async function wirft "await expressions only in async functions". Fix: `async function snapshot()`, dann im Router-Handler `async (req, res) => { const data = await snapshot() }`.
- **SQLite `ORDER BY 2` ohne Sub-Select wirft "out of range"** — bei `sqlite3 -batch` mit concat-expression: `SELECT a||'|'||b FROM ... ORDER BY 2` (Concat ist eine Expression, keine Spalte). Fix: `SELECT s||'|'||c FROM (SELECT col1 AS s, COUNT(*) AS c FROM ... GROUP BY x ORDER BY c DESC LIMIT 5)` — Sub-Select macht die Spalten explizit.

Inventur-Quick-Check bei Hermes-v7 Code-Edits: erstmal prüfen ob `import {x}` oder `const x = require(...)` — bei ESM-Projekten nie require im Source. Tritt in mehreren Code-Generation-Sessions auf.

## Pitfall 20: User-Pfad ≠ Existierender-Pfad — Pfad-Mismatch-Recovery

Wenn der User einen Pfad nennt (`/mnt/DATA/Programme/Steam/...`, `~/docs/...`, `/etc/...`), **vor dem ersten `ls`/`cat`/`read_file` IMMER verifizieren** dass der Pfad existiert. Drei Realitäten warum der Pfad nicht passt:

- **User erinnert sich falsch** (Steam-Pfade mit vs. ohne Subfolder, alte vs. neue Library)
- **Archivierung passiert automatisch** — Skills wandern nach `~/.hermes/skills/.archive/` wenn der Pattern in einen aktiven Skill konsolidiert wurde. User kennt oft nur den *historischen* Namen.
- **Symlink-/Mount-Edge-Cases** (Flatpak-Spiele, NFS-Mounts, /mnt vs. /media)

**Workflow (proven 2026-07-02):**

1. **Erst:** `ls -la "<user-pfad>" 2>&1 | head -5` — schneller Existenz-Check
2. **Bei "nicht gefunden":** `find / -maxdepth 6 -type d -name "<basename>" 2>/dev/null | head -10` — systematische Suche
3. **Skill-Lokations-Check** wenn User einen Skill-Namen nennt:
   - `ls ~/.hermes/skills/<name>/` (aktiv)
   - `ls ~/.hermes/skills/.archive/<name>/` (archiviert — nicht tot!)
4. **Bei Archiv-Treffern:** Inhalt ist NICHT veraltet, sondern konsolidiert. Im Bericht transparent machen: "Liegt im .archive-Ordner, weil der Pattern in `<active-skill>` übernommen wurde."
5. **Dem User ehrlich sagen:** "Der Pfad existiert nicht — gefunden unter X. Falls du was anderes gemeint hast, sag Bescheid." (NICHT still woanders suchen ohne den User zu informieren.)

**Anti-Pattern:** `cd <user-pfad> && cat file` ohne Existenz-Check → "nicht gefunden" als Output, User fühlt sich nicht verstanden. Besser: 5 Sekunden `find`-Aufwand, dann sauberer Pfad im Bericht.

**Merksatz:** "Der User-Pfad ist ein *Hinweis*, kein *Vertrag*. Verifiziere ihn, lokalisiere den echten Pfad, mach den Fund transparent."

---

## Quick Symptom Index

| Pitfall | One-Liner |
|---------|-----------|
| 1 | `--help` first |
| 2 | 60-120s+ timeouts |
| 3 | Need terminal+file for measurements |
| 4 | Pre-check dependencies |
| 5 | **VERIFY EVERY CLAIM** |
| 6 | Explicit OUTPUT path |
| 7 | Config writes: parent applies |
| 8 | YAML changes: parent-only |
| 9 | Set MAX 8 web-calls |
| 10 | `model` param ignored |
| 11 | Dispatch fail → parent-direct |
| 12 | Rate limits → narrow scope |
| 13 | Silent truncation: sentinel+structure check |
| 14 | Cron scripts overwrite config |
| 15 | GitHub MCP token: use `gh` |
| 16 | Queen-Lane-Plan for multi-lane missions |
| 17 | <30min lanes: parent-direct |
| 18 | Phase-0-Inventur first |
| 19 | ESM: no `require`, no top-level `await` |
| 20 | Verify user-path before `ls` |

For trigger-watchlist (when to apply each), see `multi-agent-pitfalls-cheatsheet`.