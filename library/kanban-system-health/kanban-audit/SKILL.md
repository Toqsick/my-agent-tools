---
name: kanban-audit
title: "Kanban Audit — Cross-Board Scout + Source-Code Recipe"
description: "Use when you need a cross-board complete audit, source-code implementation audit, or end-to-end coverage check across all Kanban boards. NOT for live diagnostics (use kanban-diagnostics), phases (use kanban-phases), or pitfalls (use kanban-pitfalls). Two-mode: scout-pattern (all boards) + source-recipe (per repo)."
category: kanban-system-health
version: '3.0'
created: '2026-07-23'
author: Yuno (split from kanban-system-health v2.5)
lane: koenigin
agent: universal
trigger_keywords: ['kanban', 'cross-board audit', 'scout', 'source-code audit', 'implementation drift', 'coverage check', 'all boards']
keywords: ['kanban', 'audit', 'cross-board', 'scout', 'source-code', 'implementation', 'coverage', 'all-boards']
related_skills: ['kanban-diagnostics', 'kanban-phases', 'kanban-pitfalls', 'multi-agent-kanban-audit', 'skill-reviewer']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from kanban-system-health 2026-07-23)'

license: MIT
---

# Kanban Audit — Cross-Board Scout + Source-Code Recipe

Kanban Audit — Cross-Board Scout + Source-Code Recipe

_Extracted from kanban-system-health v2.5 on 2026-07-23._

## 12. Cross-Board Complete Audit (Scout-Pattern)


**Wann:** User fragt nach vollständigem System-Status ("Scout A", "Kanban-Status", "wie sieht's aus mit allen Boards"). Keine Teil-Betrachtung — der Audit muss alle Boards erfassen.

### 12.1 Board-Scoping und der `--board`-Flag


**Seit v0.18.2 existiert ein globaler `--board <slug>` Flag** der vor dem Subcommand steht und die meisten read-only-Befehle auf ein Board beschränkt:

```bash
### 12.2 Vollständiger Cross-Board Audit (5 Steps)


#### Step 1: Alle Boards inventarisieren


```bash
hermes kanban boards list
#### Step 2: Diagnostics pro Board (mit Loop)


```bash
for board in hermes routing-lanes system voice dashboard greyhack; do
  echo "═══ $board ═══"
  hermes kanban boards switch "$board" >/dev/null 2>&1
  hermes kanban diagnostics 2>&1 | head -20
  echo ""
done
```

**Achte auf:** `stranded_in_ready`, `crashed_workers`, `stale_claims`, `repeated_failures`, `tip_scratch_workspace`.

#### Step 3: Status-Inventur pro Board


```bash
for board in ...; do
  hermes kanban boards switch "$board" >/dev/null 2>&1
  echo "═══ $board ═══"
  
  # Count by status
  for s in running ready todo blocked done; do
    cnt=$(hermes kanban list --status "$s" 2>&1 | grep -cP '^\S+\s+'"$s" || echo 0)
    [ "$cnt" -gt 0 ] && echo "  $s: $cnt"
  done
  
  # Letzte Completion finden
  hermes kanban list --status done --json 2>/dev/null | python3 -c "
import json,sys
data = json.load(sys.stdin)
if data:
    ca = max(d.get('completed_at') or 0 for d in data)
    from datetime import datetime, timezone
    dt = datetime.fromtimestamp(ca, tz=timezone.utc) if ca else None
    print(f'  last done: {dt.strftime(\"%Y-%m-%d %H:%M\") if dt else \"never\"}')
else:
    print('  last done: none')
" 2>/dev/null
done
```

#### Step 4: Blocked-Task Triage (Failure Mode Categorization)


Für jeden blocked Task: `hermes kanban diagnostics` zeigt den Grund. Zusätzlich `hermes kanban show <id>` für die letzten Events.

**Systematisch kategorisieren in 3 Failure Modes:**

| Type | Symptom in `runs` | Ursache | Fix-Kategorie |
|---|---|---|---|
| **A: Spawn/Environment** | `pid not alive`, `exited code 1`, Worker läuft nie an | Fehlende Binary, Profil nicht on-disk, Env-Config defekt | Setup fixen |
| **B: Protocol Violation** | `rc=0 without kanban_complete/block` | Worker beendet sauber aber vergisst kanban-Aufruf | Worker-Disziplin: `goal-mode` oder Verifier-Gate |
| **C: Iteration Exhausted** | `iteration_budget_exhausted (80/80)` | Scope > Iteration-Cap | Scope shrinken oder `--goal-max-turns N` erhöhen |

**Diagnose-Check für Type A (Spawn):**
```bash
#### Step 5: Standstill Detection


Ein System steht still wenn **alle 3 Bedingungen** wahr sind:

1. **Keine running Tasks** (`running = 0` über alle Boards)
2. **Keine ready Tasks** (`ready = 0` über alle Boards)
3. **Letzte Completion >48h her**

```bash
### 12.3 Coverage-Check: Skills im Kanban


`hermes kanban list --json` zeigt pro Task welche `skills` referenziert werden. Für eine Coverage-Health-Prüfung:

```bash
hermes kanban list --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
all_skills = set()
for t in data:
    for s in (t.get('skills') or []):
        all_skills.add(s)
print('Skills referenced in kanban tasks (' + str(len(all_skills)) + '):')
for s in sorted(all_skills):
    print('  -', s)
" 2>/dev/null
```

Vergleiche mit `hermes skills list | grep -c enabled` — ein Coverage-Verhältnis von <5% deutet darauf hin, dass die meisten Tasks ohne Skill-Anker laufen (weniger Steuerung über den Dispatcher, mehr Ad-hoc-Coding im Task-Body).

### 12.4 Report-Template (Scout-A Output)


Bei einem vollständigen Audit sollte die Ausgabe an den User diese Struktur haben:

1. **Audit-Zeitstempel + aktives Board** zu Beginn
2. **Aktive Boards** (Tabelle mit allen, Counts pro Status)
3. **Doing/Running-Tasks** (0 = erwähnen, das ist eine Info)
4. **Ready-Tasks** (mit Warum-wartet-es Analyse)
5. **Blocked-Tasks Triage** (kategorisiert in A/B/C Failure Modes + manuell/unassigned)
6. **Done letzte 3 Tage** (Trend sichtbar machen — Abnahme = Stillstand)
7. **Coverage Health** (Skills im Kanban vs total Skills)
8. **Worker-Profile aktiv?** (running=0? last completion?)
9. **Auffälligkeiten** (bullet points)
10. **Files erstellt/modifiziert** (für Session-Transparenz)

---

## 14. Source-Code Implementation Audit Recipe (gefunden 2026-07-13)


**Wann:** User fragt nach Source/Tests/Doku-Drift der **Implementierung** (nicht des Live-Systems). Typisch: "audit der kanban-implementierung", "ist die doku konsistent mit dem code", "was sind die versteckten annahmen im kanban-kernel". Liefert reproducible Rezept + Linenumbers + Test-Gaps.

### 14.1 Inventur (welche Module sind audit-relevant)


```bash
### 14.2 Audit-Achsen (8 unabhängige Checks, je 5-15 min)


| Achse | Was prüfen | Schlüssel-Greps |
|---|---|---|
| **State-Machine** | Atomic CAS auf `status`-Übergänge | `grep -n "WHERE status = 'ready' AND claim_lock IS NULL" kanban_db.py` |
| **Atomic Claim/Lock** | Single-DB-Writer-Discipline | `grep -n "_dispatch_tick_lock\\|write_txn" kanban_db.py` |
| **Dispatcher-Lifecycle** | Embedded-vs-standalone, singleton lock, shutdown | `grep -n "_acquire_singleton_lock\\|_release_singleton_lock" gateway/kanban_watchers.py` |
| **Failure-Breaker** | `consecutive_failures` → auto-block → recovery | `grep -n "consecutive_failures\\|failure_limit\\|reclaim_task" kanban_db.py` |
| **Board-Scoping** | `HERMES_KANBAN_BOARD` env-pin + `--board` flag | `grep -n "scoped_current_board\\|get_current_board" hermes_cli/kanban.py hermes_cli/kanban_db.py` |
| **JSON-Contracts** | Toolset-Liste, list/show shape | `grep -n "registry.register\\|kanban_show\\|kanban_list" tools/kanban_tools.py` |
| **Default-Assignee** | Profile-Resolution, fallback config | `grep -n "default_assignee\\|_default_assignee" hermes_cli/kanban_db.py` |
| **Retry/Heartbeat/Runtime** | `enforce_max_runtime`, `detect_stale_running` | `grep -n "enforce_max_runtime\\|last_heartbeat_at\\|detect_stale" kanban_db.py` |

### 14.3 Test-Selection für Audit (read-only, hermetic)


**Faustregel:** Wähle 8-12 Test-Files die alle 8 Audit-Achsen abdecken. Auswahl-Kriterium: **welche Pfade sind NICHT durch `test_kanban_core_functionality` (168 Tests, der Catch-All) abgedeckt?**

```bash
### 14.4 Befund-Template für User-Lieferung


Pitfall #27-29 in §10 plus dieser Struktur:

1. **Drift-Befund** — Workspace-HEAD vs vom User genannte Version/SHA. Wenn SHA nicht existiert, explizit sagen (NICHT stillschweigend überspringen).
2. **Test-Resultate** — echte pytest-Outputs mit Counts (passed/failed/xfailed/skipped). 227/227 ist gut, ein einzelner xfail braucht Diskussion.
3. **Source:Line-Belege pro Audit-Achse** — jeder Befund hat mindestens eine Linenumber. Pattern: `<modul>.py:<zeilennr> — <kurze Interpretation>`.
4. **Confirmed Bugs vs. Risks** — trennen! "Bestätigter Bug" = reproduzierbar oder gegen Test gesichert. "Risiko" = theoretisch oder Design-Limitation.
5. **Drift-Bugs / Doku-vs-Code** — Modul-Doc-Strings die auf nicht-existente Files zeigen, `pyproject.toml` Version vs Realität.
6. **Fehlende Tests** — welche Pfade keine Coverage haben (siehe Pitfall #29 für den 2026-07-13-Stand).
7. **Konkreter Patch-Plan** — nummerierte Liste, **nicht ausgeführt** (read-only Audit).

### 14.5 Wann Source-Audit vs. Cross-Board-Audit


| Audit-Typ | Ziel | Live-System nötig? | Schema-only reicht? |
|---|---|---|---|
| Cross-Board-Audit (§12) | Live-Tasks, Stuck-Detection, Failure-Modes | Ja (sqlite mode=ro reicht) | Nein |
| **Source-Audit (§14)** | Code-Korrektheit, Drift, Coverage | Nein (rein Source/Tests/Doku) | Ja |
| Security-Audit (§8.1) | Token-Leaks, Permissions | Ja (.env lesen) | Nein |

Falls User "Kanban audit" ohne Spezifikation sagt: zuerst fragen welche Achse. Default für technische Reviews ist Source-Audit, für Operations ist Cross-Board-Audit.

---

## 13. Verwandte Skills + Doku


- `kanban-orchestrator` (v3.0.0) — Decomposition-Playbook für Orchestrator-Profile
- `kanban-worker` (v2.0.0) — Worker-Pitfalls und Lifecycle
- `kanban-codex-lane` (v1.0.0) — Dual-Lane mit Codex als Sub-Worker
- `yuno-team-orchestrator` — Routing-Engine für 7 Personas (anderes Multi-Agent-System, nicht Kanban-spezifisch)
- `kanban-system-health/references/2026-07-09-session-evidence.md` — **Live-verifizierte Daten** aus den 2026-07-09 Sessions (Skill-Mapping-Tabelle, Worktree-Test, Auto-Decomp-Beweis, 6-Bienen-Resultate, Secrets-Audit-Findings, Hermes-Dashboard-Auth-Block, File-Attachment-Test). Empirische Grundlage für die v2.0.0-Patches.
- `kanban-system-health/references/sync-engine-roundtrip-2026-07-09.md` — **Sync-Engine-Roundtrip-Test** vom 2026-07-09. Vollständige db_to_md→MD-Edit→md_to_db→auto-Verifikation mit 5 Edge-Cases (create_task-default, Logging-Granularität, case-sensitive Section-Header, Placeholder-Verhalten, Roundtrip-Idempotenz). CLI-Befehle für schnelle Wiederholung enthalten. Production-Ready-Empfehlung für Cron-Betrieb.
- `kanban-system-health/references/kanban-worker-toolset-and-json-drift.md` — **Worker-Toolset-Drift + JSON-Shape-Drift** (gefunden 2026-07-11). Zwei Live-Bugs die jeder Setup-Script-Generator und jeder Monitoring-Code kennen muss: (a) Workers werden via `platform_toolsets.cli` resolved, nicht via Top-Level `toolsets` — Setup-Scripts die nur `toolsets` schreiben spawnen Worker mit falscher Tool-Liste; (b) `kanban list --json` enthält keine Run-Felder, `kanban show --json` liefert sie unter `runs[-1]` — naive Enrich-Loops verlieren STUCK/OVERTIME-Detection still. Mit Reproduktion, Audit-Recipe und Fix-Pattern.
- `kanban-system-health/references/scout-a-kanban-audit-2026-07-11.md` — **Cross-Board Complete Audit Live-Evidence** (gefunden 2026-07-11). Vollständiger 5-Step Audit über 7 Boards mit 62 Tasks. Enthält: 14x Blocked-Task Triage kategorisiert in 3 Failure Modes (A: Spawn/Environment, B: Protocol Violation, C: Iteration Exhausted) + Standstill-Detection (0 running, 0 ready, >48h ohne completion) + Coverage-Health (3/263 Skills im Kanban = 1.1% Ratio) + verifizierte Board-Scoping-Facts. Empirische Grundlage für §12 Cross-Board Complete Audit Pattern.
- `kanban-system-health/references/kanban-implementation-source-audit-2026-07-13.md` — **Source-Code Implementation Audit Recipe** (gefunden 2026-07-13). Vollständiges reproduzierbares Rezept für read-only Source/Tests/Doku-Drift-Audits der Kanban-Implementierung. 8 audit-relevante Source-Module + 30 Test-Files + 3 Doku-Files, 8 unabhängige Audit-Achsen mit Schlüssel-Greps, 11-File-Pytest-Selector mit 227 Tests, Befund-Template. Verifiziert gegen Workspace-HEAD `ac705b52c`, Version 0.18.2. Empirische Grundlage für §14 und Pitfalls #27-29.
- `kanban-system-health/references/dispatcher-stale-lock-and-gateway-death-2026-07-11.md` — **Dispatcher Stale Lock + Gateway Death** (gefunden 2026-07-11, korrigiert 2026-07-13). Dreifach-Bestätigung dass Gateway down = Dispatcher down = ready-Tasks akkumulieren, während der Cron-Ticker „alles läuft“ vortäuscht. **Korrektur 2026-07-13:** Lockdatei-Attribute (`size=0`, `mtime>5min`) sind **kein** Health-Signal — die Datei ist nur Inode für `fcntl`/`msvcrt`. Echte Probe: non-blocking `flock`. Recovery-Sequenz + 4 Lessons Learned.
- `kanban-system-health/references/kanban-correctness-audit-2026-07-13.md` — **Vollständiger Kanban Correctness-Audit** (gefunden 2026-07-13). Live-Inventur 7 Boards, 73 Tasks, 14 blocked Triage in 3 Failure Modes, Zombie-Run `t_ff13b7c7` mit Cleanup-SQL, 18 Test-Fixture-Leakage-Befunde (alle Tests einzeln grün), 2 falsche Diagnose-Regeln aus dem 2026-07-11-Audit widerlegt (Lock-Spur, Spec-PDF-Existenz), priorisierte Verbesserungsmatrix P0-P3 mit Verifikations-Ketten.

**Verwandte Doku in `~/docs/system/`:**
- `kanban-multi-agent-status-2026-07-09.md` — Initial-Report
- `kanban-coverage-map-install-plan-2026-07-09.md` — Coverage-Matrix + 4-Phasen-Plan
- `kanban-phase-0-1-run-2026-07-09.md` — Phase 0+1 Run-Log
- `kanban-phase-2-4-run-2026-07-09.md` — Phase 2-4 Run-Log
- `kanban-phase-5-plan-2026-07-09.md` — Phase 5 Plan
- `kanban-best-practices-2026-07-09.md` — 5 Task-Templates
- `kanban-session-final-2026-07-09.md` — Final-Synthese
- `hermes-profile-skill-map-2026-07-09.md` — Goal-Mode-Output (alle 6 Profile)
- `secrets-audit-2026-07-09.md` — 🚨 Security-Audit-Findings

---

## Changelog


- `2.5.0 (2026-07-20)` — **Hermes-v2-Konsolidierung (Plan-Task H-62).** Pitfall #17 (Worker-Toolset-Resolution-Drift) als **GELÖST** markiert — H-07-Drift-Guard `~/.hermes/scripts/check_toolset_drift.py` fängt den Drift jetzt über den echten Resolver `_get_platform_tools(cfg,"cli")` ab (nächtlich via H-34). Drei neue Pitfalls: #34 (hermes-CLI-Exitcodes IMMER 0, `main.py:15290-15291` verwirft `args.func`-Return → nur stdout/JSON parsen; Chip `task_575d3b49`), #35 (`source ~/.hermes/.env` seit H-04 kaputt wg. unquotiertem bcrypt-Hash → gezielte `grep|tail|cut`-Extraktion), #36 (Board-Dispatch fail-closed, `dispatchable: false` ist kein Bug). Neuer §15 „Hermes-v2-Betrieb": Update-Hazard-Prozedur (jeder `hermes update` resettet `hermes-v2-work`→`main` und entfernt Core-Patches + P-71-Guard), P-71 Board-scoped Dispatch-Guard + beide Spawn-Sturm-Postmortems (22 Worker / 2×5 Worker), Cron-Trio H-34/H-53/H-54 (User-Crontab-Entscheid, Henne-Ei), Dispatcher-Instabilität (`pid not alive`), UI-Single-Source (H-30 hermes-webui `:8787`), Coding-Pipeline (H-31), Swarm-v2-Routing (H-41, `swarm_routing.py` + 7 `swarm.*`-Keys). §7.2 Querverweis auf die UI-Entscheidung. Frontmatter: 6 neue Tags, 10 neue Triggers (u. a. „coding pipeline", „dispatch guard", „nach hermes update"). Begleit-Runbook: `~/20-Workspace/results/h62-ops-runbook/OPS-RUNBOOK.md`. 36 Pitfalls total.

- `2.4.1 (2026-07-13)` — **Audit-Round-2 (2026-07-13 Correctness-Audit).** Pitfall #30 erweitert um die härtere `sys.modules`-Reimport-Variante (gefunden via `test_kanban_default_assignee.py::isolated_kanban_home` der `hermes_cli.plugins` komplett aus `sys.modules` löscht — orphaned das `_plugin_manager`-Global). Neuer Pitfall #33: `hermes-gateway.service` Unit-Datei existiert aber systemd kennt sie nicht (`list-unit-files` zeigt `not-found`) — Root-Cause für „Service startet nicht obwohl Unit da ist". Inkl. vollständige 4-Schritt-Diagnose-Kette + 3-Schritt-Fix (`daemon-reload` zuerst) + optionalem Unit-Hardening mit `Restart=on-failure`. 33 Pitfalls total. §1.3 Lock-Probe: ersetzt die widersprüchliche Inline-„stale >5 min"-Empfehlung durch die korrekte non-blocking `flock`-Probe (Synchronisation mit Pitfall #22). §10: Drei neue Pitfalls #30 (Test-Fixture-Leakage via Singleton-PluginManager mit reproduzierbarem Isolated-vs-Full-Run-Symptom + Fix-Pattern), #31 („Standstill" ≠ Bug — korrigierte Heuristik: Standstill OHNE ready UND OHNE Dispatcher ist Cron-only-Modus, kein Bug), #32 (`notify-subscribe`/`unsubscribe` Subcommands vs `notification_sources`-Config — beide Subscriptions-Mechanismen, nicht vermischen). Pitfall #22 in §1.3 jetzt explizit mit ⚠️-Warnung gegen den früheren `stat`-Lock-Befund-Trugschluss. Stand der Pitfalls: 32. Added reference `kanban-correctness-audit-2026-07-13.md` (Vollständiger Audit-Bericht: 7 Boards, 73 Tasks, 14 blocked, Failure-Mode-Triage A/B/C, Zombie-Run-Detection, 18 Test-Fixture-Leakage-Befunde, alle Empfehlungen mit read-only-Verifikation). §14 komplett neu: reproduzierbares Rezept für read-only Source/Tests/Doku-Drift-Audits der Kanban-Implementierung (Inventur 8 Module + 30 Tests + 3 Doku-Files, 8 unabhängige Audit-Achsen mit Schlüssel-Greps, 11-File-Pytest-Selector mit 227 Tests, Befund-Template, Source-Audit vs. Cross-Board-Audit Entscheidungsmatrix). §10: Drei neue Pitfalls #27 (Modul-Doc-String verweist auf nicht-existente Spec-PDF `docs/hermes-kanban-v1-spec.pdf`), #28 (Goal-Mode Judge-Gate ist fail-open, kein hartes Protocol-Complete-Enforcement — wer das behauptet lügt), #29 (Test-Coverage-Lücken in `_check_dispatcher_presence`, `--board`-Pre-Check, Singleton-Lock-Branches, `_profile_author`, `_task_summary_dict`, `_handle_comment`). Added reference `kanban-implementation-source-audit-2026-07-13.md` mit vollständigem Audit-Transkript (Pytest-Outputs, Linenumber-Belege pro Achse, Patch-Plan). Removed stale reference `read-only-cross-board-audit-2026-07-13.md` (file did not exist on disk despite description claim). 29 Pitfalls total.

- `2.3.0 (2026-07-13)` — **Read-Only Cross-Board Audit Recipe + 3 neue Pitfalls.** §12.1 komplett überarbeitet: dokumentiert den seit v0.18.2 existierenden globalen `--board <slug>` Flag (Variante B für Cross-Board-Audits ohne Side-Effect auf `~/.hermes/kanban/current`). §10: Drei neue Pitfalls #24 (Zombie-Run ohne Task-Zeile, mit Detection-Query + Hardline-Cleanup), #25 (Timestamps sind Sekunden, nicht ms — Verifizierungs-Rezept via `datetime(x,'unixepoch')`), #26 (`task_runs.status` Schema-Drift `done` vs `completed` mit Cleanup-Warnung). Pitfall #20 **korrigiert**: zeigt jetzt dass `--board` als globaler Flag existiert und bleibt nur beim Cross-Board-Pitfall (Task-IDs silent-fail bei falschem Board). Added reference `read-only-cross-board-audit-2026-07-13.md` mit Reproduktions-Rezept für SQLite-Read-Only-Audits, Zombie-Run-Transkript und 73-Task-Cross-Board-Evidenz. 26 Pitfalls total.

- `2.2.0 (2026-07-11)` — **Scout-C Dispatcher-Death + Cron-Pinning Pitfalls.** §1.3: Ergänzt embedded-Dispatcher-Death-Caveat (Gateway down = Dispatcher down, Cron-Ticker täuscht) mit 3-Stufen-Verifikationskette. §2: Hypothese 5 erweitert mit Gateway-First-Check und Recovery-Sequenz. §10: Zwei neue Pitfalls #22 (Stale Dispatcher Lock) und #23 (Embedded-Dispatcher-Death). Added reference `dispatcher-stale-lock-and-gateway-death-2026-07-11.md` mit Live-Befunden und Recovery-Rezept. 23 Pitfalls total.

- `2.1.0 (2026-07-11)` — **Scout-A Cross-Board Complete Audit Pattern.** Added §12 Cross-Board Audit (Board-Scoping-Facts, 5-Step Cross-Board Audit, 3 Failure Modes A/B/C, Standstill Detection, Coverage Check, Report-Template). Added Pitfalls #20 (board-scoped show/list) und #21 (3 Failure Modes). Added reference `scout-a-kanban-audit-2026-07-11.md` mit 62-Task-Live-Evidence von 7 Boards. 21 Pitfalls total.

- `2.0.0 (2026-07-09)` — **MAJOR UPDATE basierend auf Phase 0-4 + 6 Bienen-Outputs.** Reorganized in 12 Sektionen mit Quick-Start-Phase-Map. Added Phase 0-4 Operations-Playbook (Cleanup → Assignment → Worker-Maturity → Advanced-Patterns → Dashboard). **14 Pitfalls** (von 6). Added Templates für Swarm/Auto-Decomp/Goal-Mode/Worktrees. Added 2-Wellen-Bienen-Pattern. Added Skill-Mapping-Tabelle (Per-Profile-Lookup). Added Dashboard-Auth-Workaround. Added Security-Audit-Pattern (🚨 P0). Added File-Attachments End-to-End-Test-Pattern. Coverage 40% → 88%.
- `1.1.0 (2026-07-09)` — Added Schritt 0 (built-in `hermes kanban diagnostics` + `assignees` VOR manuellen SQL-Queries, gelernt aus Coverage-Map-Session). Added Pitfall #6 (built-in diagnostics ignorieren) + Sub-Pitfall per-Board-DB-Struktur.
- `1.0.0 (2026-07-09)` — Initial. Live-State-Check-Reihenfolge, 4-Hypothesen-Diagnose, Reaktivierungs-Steps, 5 Pitfalls aus der 2026-07-09 Status-Untersuchung.
