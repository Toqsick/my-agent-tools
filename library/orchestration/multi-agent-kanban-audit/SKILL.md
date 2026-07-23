---
name: multi-agent-kanban-audit
description: |
  Use when you need to use the multi-agent-kanban-audit workflow and its documented procedures.
  NOT for unrelated tasks outside the multi-agent-kanban-audit workflow.
  Provides focused guidance for multi-agent-kanban-audit.
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags:
    - Multi-Agent
    - Kanban
    - Hermes
    - Audit
    - Recovery
license: MIT
trigger_keywords: ['multi', 'agent', 'kanban', 'audit', 'workflow']
keywords: ['multi', 'agent', 'kanban', 'audit', 'workflow']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['voice-clone', 'multi-agent-pitfalls-cheatsheet', 'kanban-orchestrator']
---

# Multi-Agent Kanban Audit & Revival

Wakes up a dormant Hermes multi-agent kanban (ready-Tasks stranded, dispatcher silent, 0% Worker-Activity) and brings it to production-grade in 4 documented phases. Stdlib + `hermes` CLI only; no new dependencies.

## When to Use

- Kanban shows >10 ready-Tasks but **none dispatched** for hours/days
- Worker-Spawn fails with "Unknown skill(s): …" — **Per-Profile Skill-Lookup-Mismatch**
- Profile-Descriptions empty → Auto-Decompose + Swarm-Routing greift nicht
- Biene-Output delivered but the Worker-Output-File is **missing the file-attachments or summary**
- Coverage-Map < 50% across Core-Concepts / Worker-Lane / Advanced-Patterns

## Prerequisites

- `hermes` CLI on `$PATH` (`pip install hermes-agent` or `~/.hermes/hermes-agent/venv/bin/hermes`)
- `python3` + `sqlite3` CLI (stdlib)
- Read-only access to `~/.hermes/config.yaml`, `~/.hermes/profiles/*/`, `~/.hermes/kanban/boards/*/kanban.db`
- Optional: `mnemosyne` Python-package for memory-health-check
- **Read-only-first convention**: always produce a coverage-map and assign/block-plan BEFORE touching config

## How to Run

Invoke through the `terminal` tool. The procedure is **4 phases, ~3.5 Std total**, each ending in a Markdown report under `~/docs/system/`.

## Quick Reference

| Phase | Goal | Dauer | Output-Datei |
|---|---|---|---|
| 0+1 | Diagnose + Assign blocked-ready Tasks | 1.25 Std | `kanban-multi-agent-status-*.md` |
| 1.5 | E2E-Multi-Swarm-Probe (optional) | 0.15 Std | `/tmp/swarm-probe-*.md` |
| 2 | Worktree/Max-Runtime/Goal-Mode aktivieren | 0.75 Std | `kanban-best-practices-*.md` |
| 3 | Auto-Decomp + Swarm-Dispatch produktiv | 0.75 Std | Run-Log |
| 4 | 6-Bienen 2-Wellen-Dispatch + GC | 0.75 Std | `kanban-session-final-*.md` |

**Coverage-Ziel:** 40% → 88% in einer Session.
**E2E-Multi-Swarm-Probe:** bewiesen 2026-07-20 20:30–20:40, gate=pass, 10 Min, /tmp/kanban-overview-2026-07-20.md (28 Zeilen, SHA256 verifiziert).

## Procedure

### Phase 0+1: Diagnose + Routing (1.25 Std)

1. **Read-only snapshot der Lage** via `terminal`:
   ```bash
   hermes profile list
   for board in routing-lanes hermes system voice dashboard greyhack; do
     hermes kanban boards switch "$board" >/dev/null 2>&1
     sqlite3 ~/.hermes/kanban/boards/$board/kanban.db "SELECT status, COUNT(*) FROM tasks GROUP BY status"
   done
   ```
2. **Identify stranded-ready**: alle Tasks mit `status='ready' AND assignee=''` → das ist das Symptom
3. **Set Profile-Descriptions** via `hermes profile describe <name> --text "..."` für jedes Profile das Worker spaw­nen soll. Ohne Description weiß der Decomposer nicht wohin routen.
4. **Backup** vor jeder Mutation: `cp -r ~/.hermes/kanban ~/50-System/backups/kanban-pre-coverage-$(date +%Y-%m-%d)/`
5. **Diagnose-Wurzelfehler Crashes** (siehe Pitfalls):
   ```bash
   hermes kanban diagnostics  # zeigt stranded/blocked mit Begründung
   ```
6. **Assign oder Block** jedes stranded-Task mit Begründung — keine offenen ready lassen
7. **Worker-Crash-Pattern** "Error: Unknown skill(s): X":
   ```bash
   # Welche Skills hat das Ziel-Profil?
   find ~/.hermes/profiles/<current-profile>/skills -name "<X>*"
   # Wenn 0 Treffer: Skill-Lookup ist per-Profile!
   # Fix:
   hermes kanban reassign <task-id> yuno --reclaim --reason "Skills fehlen in <old-profile>"
   ```

### Phase 1.5: E2E-Multi-Swarm-Probe (10-15 Min)

Optional aber empfohlen: beweise die Top-Down-Pipeline bevor du komplexe Multi-Agent-Operationen startest.

8. **Mini-Schwarm mit `hermes kanban swarm`** auf aktivem Board:
   ```bash
   hermes kanban swarm "<kompaktes Goal mit max 30 Zeilen Output-Spec>" \
     --worker "yuno-flash:<Title1>:<skill-in-yuno-flash>" \
     --worker "yuno-coder:<Title2>:<skill-in-yuno-coder>" \
     --verifier yuno-coder \
     --synthesizer yuno-coder \
     --created-by yuno \
     --idempotency-key <unique-key>
   ```
   Erzeugt automatisch 5 Tasks: 1 Root done + 2 Worker ready + 1 Verifier todo + 1 Synthesizer todo
9. **Worker-Spec-Skills MÜSSEN im Zielprofil vorhanden sein** — sonst Crashes. Vorher prüfen:
   ```bash
   ls ~/.hermes/profiles/<ziel-profile>/skills/ | grep <skill-name>
   ```
10. **Auto-Dispatch greift** wenn Board `dispatchable: true` — Worker spaw­nen innerhalb 60s nach swarm-Befehl.
11. **Topology-Demo:** Verifier wartet auf Workers done → Synthesizer wartet auf Verifier done. Auto-Promote via `recompute_ready`.
12. **Endstand:** Synthesizer schreibt disk-Output (z.B. `/tmp/probe-output.md`), SHA256 wird von Verifier validiert.
13. **Snapshot-Drift:** Verifier flaggte live-vs-snapshot-Unterschiede, Synthesizer fixt im Final-Output.

### Phase 2: Worker-Maturity (0.75 Std)

8. **Best-Practices-Guide** schreiben mit allen Flags (`kanban-best-practices-*.md`)
9. **Test-Tasks mit allen Flags** erstellen (siehe Pitfalls zu Edit-Command):
   ```bash
   # A) Code-Task mit Worktree
   hermes kanban boards set-default-workdir <board> ~/path/to/git-repo
   hermes kanban create "<title>" --assignee yuno-coder --workspace worktree \
     --branch feat/<name> --skill software-development/<skill> --max-runtime 3600

   # B) Cron-Task mit Idempotency
   hermes kanban create "<title>" --assignee yuno --skill yuno-cleaner \
     --idempotency-key nightly-<date> --max-runtime 1800

   # C) Langläufer mit Goal-Mode
   hermes kanban create "<title>" --assignee yuno --goal --goal-max-turns 20 \
     --max-runtime 5400
   ```
10. **Verification**:
    ```bash
    sleep 75 && hermes kanban boards switch <board> >/dev/null && \
      herem kanban list --status running | grep t_<id>
    # Git-Worktree erstellt:
    git -C ~/path/to/git-repo worktree list
    ```

### Phase 3: Auto-Decomp + Swarm (0.75 Std)

11. **Config setzen** (alle 4 Werte):
    ```bash
    hermes config set kanban.orchestrator_profile "yuno"
    hermes config set kanban.default_assignee "yuno"
    hermes config set kanban.auto_subscribe_on_create true
    hermes config set auxiliary.kanban_decomposer.model "MiniMax-M3"
    # WICHTIG: notification_sources wird als String gespeichert, nicht YAML-Liste!
    # Manuell in ~/.hermes/config.yaml:
    #   notification_sources:
    #     - '*'
    ```
12. **Showcase-Swarm** dispatched (verifiziert das Pattern):
    ```bash
    herem kanban boards switch routing-lanes
    hermes kanban swarm "<goal>" --max-turns 15
    # Erzeugt: 1 root + 2 worker + 1 verifier + 1 synthesizer
    ```
13. **Auto-Decompose testen** via Triage-Status:
    ```bash
    hermes kanban create "Bau ein <feature>" --triage --body "<detailliert>" \
      --assignee yuno --max-runtime 7200
    # Nach 60-90s: 6 Sub-Tasks automatisch, jeder mit eigenem Assignee
    ```

### Phase 4: 6-Bienen 2-Wellen-Dispatch (0.75 Std)

14. **Welle 1: 3 Bienen simultan**, jede mit eigenem Board + Profile:
    ```bash
    herem kanban boards switch routing-lanes
    hermes kanban create "Biene-1: <audit>" --assignee yuno-coder --max-runtime 1200
    herem kanban boards switch hermes
    hermes kanban create "Biene-2: <cleanup>" --assignee yuno-coder --max-runtime 1200
    herem kanban boards switch greyhack
    hermes kanban create "Biene-3: <coverage-map>" --assignee yuno-coder --max-runtime 1200
    ```
15. **Welle 2: 3 weitere** nach 5s Delay (gleiche Syntax, andere Boards)
16. **Workspace GC** nach Bienen-Completion:
    ```bash
    hermes kanban gc  # default 30 Tage retention
    ```
17. **Final-Report** schreiben mit allen Metrics: Coverage-Delta, Tasks done, Files erstellt

## Pitfalls

1. **`hermes kanban edit`** ist NUR für done-Tasks. Für ready/blocked → reassign oder recreate. **Häufigster Fehler**.
2. **Skill-Lookup ist per-Profile**, nicht global. `default`-Profile hat oft 0 Skills im neuen Profile-System → **niemals als Worker nutzen**. Vor jeder Assignierung: `find ~/.hermes/profiles/<profile>/skills -name "<skill>*"`
3. **Worktree braucht Board-Default-Workdir in Git-Repo**, nicht in Multi-Repo-Ordnern. Symptom: "task has workspace_kind=worktree but no workspace_path, and board 'X' has no default_workdir set" → `hermes kanban boards set-default-workdir <slug> <git-repo-path>`
4. **`hermes config set` speichert Listen als String**, nicht als YAML-Liste. Für echte Listen: direkt `~/.hermes/config.yaml` editieren oder vorher prüfen dass der Wert als Liste ankommt.
5. **`hermes kanban block <id> <kind> <reason>`** — kind ist positional (`incomplete`/`needs-info`/`self-ref`), nicht `--kind` Flag.
6. **`hermes kanban archive`** hat kein `--reason`-Flag — Comment vorher via `hermes kanban comment <id> "<reason>"` anlegen.
7. **Auto-Decompose** ruft nur 1× pro Dispatch-Tick auf und max 3 Tasks gleichzeitig. Bei >3 Triage-Tasks wartet der Rest bis nächsten Tick.
8. **Circuit-Breaker** triggert nach `failure_limit: 2` (Default in config.yaml). 2 Crashes = auto-blocked. Fix: `hermes kanban unblock <id> --reason "..."` dann Workdir/Profile fixen.
9. **Notification-Sources Format**: YAML-Liste mit `['*']` nicht `'["*"]'` (String-Form). Direkt in der YAML editieren.
10. **Dashboard-Auth** (Bonus): Hermes Dashboard Auth-Middleware greift für alle `/api/` Routen, auch loopback. Workaround: `hermes serve` (Port 34647) headless API nutzen statt Dashboard-GUI.
11. **`hermes kanban boards set-dispatch`** Token ist `on`/`off`, NICHT `true`/`false`. Erforderlich nach jeder Board-Mutation wenn Dispatcher-Schutz gewünscht.
12. **`hermes kanban claim` lehnt ab** wenn Parents NOT IN (`done`, `archived`). `force-promote` reicht NICHT — Invariante im Code `kanban_db.py:3599-3623` erzwingt das hartnäckig. **Workaround: Standalone-Task ohne Parents erstellen** (`hermes kanban create ...` ohne `--parent`).
13. **Dispatcher dispatcht JEDES ready+assigned** auf dem aktiven Board, nicht nur den spezifizierten Task. **Schutz:** andere ready Tasks vorher `block`en mit Begründung, oder `--max 1` mit `set-dispatch off`/`on` pro Board.
14. **`hermes kanban claim` ohne nachfolgendes `dispatch`** setzt status=running ohne Worker-PID — Inkonsistenz (kein Worker vorhanden aber Status running). Immer via `hermes kanban dispatch` sauber starten.
15. **Leere Swarm-Tasks** (Title="t", Body=leer, 170h alt) entstehen wenn Swarm auto-promoted aber Workers nie gecrasht sind. Diagnostics zeigt "Ready for Xh with no worker" mit `assignee=worker`. Vor Re-Launch: prüfen ob Body+Parent-Topologie noch sinnvoll, sonst archivieren.
16. **`hermes kanban swarm` E2E-Pitfalls:** Worker-Spec Format ist `PROFILE:TITLE[:SKILL,SKILL]` — Skills MÜSSEN im Zielprofil installiert sein (siehe Pitfall #2). Bei falschem Skill crashed der Worker mit exit_code 1 + log "Error: Unknown skill(s): <name>". Circuit-Breaker triggert nach 3 Crashes. **Workaround:** Skill im Profil nachinstallieren ODER reassign auf Profil das Skill hat.
17. **Force-Promote vs. Parents-Done:** `promote --force` setzt Status auf `ready`, aber der nächste `claim`/`recompute_ready`-Tick demoted zurück auf `todo` wenn Parents NOT IN (done,archived). **Workaround für Top-Down-Pipeline mit teilweise failed Workern:** den failed Worker `archive`n (hebt Parents-Constraint auf), dann promote Verifier/Synthesizer. Im Audit-Trail ist archive-Begründung dokumentiert.
18. **Snapshot-Drift-Detection:** Verifier dokumentiert live-vs-snapshot-Unterschiede (seit Worker-2-Snapshot sind Tasks weitergewandert: done/archived). Synthesizer hat Action-Item "refresh board row and ready list against live DB before final delivery". Default-Verhalten ist gut, aber bei langen Swarms (>10 Min) wahrscheinlich relevant.

## Verification

Single command proving the audit + revival worked:

```bash
# Erwartet: Coverage 88%+, 0 stranded ready, alle Profile mit Description
for board in routing-lanes hermes system voice dashboard greyhack; do
  hermes kanban boards switch "$board" >/dev/null 2>&1
  echo "$board: $(hermes kanban list --status ready 2>/dev/null | grep -c ready) stranded ready"
done
# Alle Boards sollten 0 stranded ready zeigen
```

Plus das **Smoke-Test-Sample**: 9/13 dispatched Tasks done in den ersten 25 Min, alle Health-Checks PASS im Audit-Report.