# Scout A: Kanban State Audit — 2026-07-11

**Zweck:** Diese Reference-Datei dokumentiert die Live-Daten des Scout-A Cross-Board Audits vom 2026-07-11. Sie validiert die §12 Cross-Board Complete Audit Patterns in SKILL.md.

---

## Audit-Kontext

- **Epoch (UTC):** 1783794551 = 2026-07-11 18:29 UTC
- **Aktives Board zu Beginn:** `hermes`
- **Shell:** bash (Zorin OS 18.1, Linux 6.17.0-35-generic)
- **Letzte Completion vor Audit:** 2026-07-09 11:52 UTC (~54h Standstill)

---

## Boards-Inventar (7 Boards)

| Board | Slug | Blocked | Done | Todo | Ready | Running | Archived |
|---|---|---|---|---|---|---|---|
| Hermes V7 + Orchestrierung | `hermes` | 5 | 12 | 4 | 0 | 0 | 0 |
| Yuno Dashboard | `dashboard` | 3 | 1 | 0 | 0 | 0 | 0 |
| GreyHack Tools | `greyhack` | 4 | 2 | 0 | 0 | 0 | 0 |
| System Fixes & Maintenance | `system` | 1 | 3 | 0 | 0 | 0 | 0 |
| Voice Bot Pipeline | `voice` | 1 | 2 | 0 | 0 | 0 | 0 |
| 3-Lane Routing Swarms | `routing-lanes` | 0 | 30 | 0 | 0 | 0 | 5 |
| Default | `default` | 0 | 0 | 0 | 0 | 0 | 0 |

**Total:** 14 blocked, 50 done, 4 todo, 0 ready, 0 running

---

## Blocked-Task Triage (14 Tasks, 3 Failure Modes)

### Type A: Spawn/Environment Crash (5 Tasks)

Worker läuft nie an — PID stirbt sofort oder existiert nicht.

| Task-ID | Board | Assignee | Runs | Symptom |
|---|---|---|---|---|
| t_629a486c | hermes | default | 2 | `crashed` ×2: pid 145761 exited code 1 / pid 146383 not alive |
| t_b5355095 | hermes | default | 2 | Gleiches Muster: pid 146384 not alive |
| t_3e301aff | hermes | default | 2 | Gleiches Muster: pid 146385 not alive |
| t_695bf28b | voice | yuno | 2 | `crashed`: pid 291988 exited code 1 |
| t_f5b8cc22 | dashboard | (unassigned) | 0 | Keine Runs — nie dispatched (kein assignee) |

**Diagnose:** Alle 3 `default`-Profile-Tasks crashed mit identischem Muster. `default`-Profil hat 0 Skills und ist kein gültiges Worker-Profil.

### Type B: Protocol Violation (2 Tasks)

Worker läuft sauber durch (rc=0) aber ruft weder `kanban_complete` noch `kanban block` auf.

| Task-ID | Board | Assignee | Runs | Symptom |
|---|---|---|---|---|
| t_f52972de | hermes | ui-builder | 2 | Beide Runs: `protocol_violation` rc=0 — Worker exit ohne kanban-Benachrichtigung |
| t_27ae33f1 | dashboard | yuno-coder | 2 | `protocol_violation` rc=0 — gleiches Muster |

**Diagnose:** `ui-builder` Profil ist nicht on-disk — `hermes kanban assignees` zeigt `on disk = no`. Worker aus nicht-existentem Profil können nicht korrekt kommunizieren.

### Type C: Iteration Budget Exhausted (2 Tasks)

Worker hat maximale Iterationen erreicht ohne Aufgabe abzuschließen.

| Task-ID | Board | Assignee | Runs | Symptom |
|---|---|---|---|---|
| t_8482eeab | hermes | yuno | 2 | `iteration_budget_exhausted 80/80` ×2 — self-referential (test kanban via kanban) |
| t_d2470bd4 | dashboard | yuno-coder | 2 | `iteration_budget_exhausted 80/80` ×2 — PWA-Install Support zu komplex |
| t_4dd67711 | greyhack | yuno | 2 | `iteration_budget_exhausted 60/60` ×2 — suid_exploit remote mode zu umfangreich |

### Manuell / Unassigned (4 Tasks)

| Task-ID | Board | Grund | Fix |
|---|---|---|---|
| t_8e3f4724 | greyhack | In-Game Mission (Reraldi@adahidomev.net) | Basti muss spielen |
| t_00244d6c | greyhack | In-Game Smoke-Tests (19 Tools) | Basti muss testen |
| t_a5e0398d | system | EDID-Fix: Reboot durchführen | Basti muss rebooten |
| t_5e94e7e6 | greyhack | Refactor: suid_exploit.py Type Hints + Tests | Re-promote (war vorher ready, durch Session-Ende gestrandet) |

---

## Standstill-Analyse

- **Letzte Completion über alle Boards:** 2026-07-09 11:52 UTC (t_a8979c00 Biene-5, Tool-Coverage-Audit)
- **Seit ~54h kein einziger Task dispatched oder completed**
- **Keine ready-Tasks** = Dispatcher hat nichts zu tun
- **Keine running-Tasks** = Kein Worker aktiv
- **4 todo-Tasks** warten auf completion ihrer parents (alles Schatten des Doku-Swarms vom Juni)

**Ursache:** Der Dispatcher ist aktiv (Gateway läuft) aber es gibt keine ready-Tasks — alle sind entweder blocked, todo, oder done. Der Standstill ist ein "leerer Tank", kein Dispatcher-Problem.

---

## Coverage-Health

| Metrik | Wert |
|---|---|
| Skills enabled total | 263 |
| Skills referenced in Kanban (hermes-board) | 3 (humanizer, requesting-code-review, system-documentation) |
| Skill Coverage Ratio | ~1.1% |
| Profile aktiv genutzt | `yuno-coder` (9 done), `yuno` (3 done) |
| Profile idle | `yuno-flash`, `yuno-vision`, `local-9b` |
| Profile defekt | `ui-builder` (on disk = no), `default` (0 Skills) |

---

## Verifizierte Board-Scoping-Facts

Die folgenden Facts wurden **durch echte Tool-Calls live verifiziert**:

1. **Task-ID Resolution ist Board-scoped:** `hermes kanban show t_d2470bd4` auf dem hermes-Board gibt `"no such task"` — Task ist auf dem dashboard-Board.
2. **Kein `--board` Flag:** Alle Versuche, einen Board-weiten `show`/`list` Befehl zu finden, schlugen fehl. Einziger Weg: `boards switch` + dann Befehl.
3. **`hermes kanban list --json` variiert pro Board:** Jedes Board hat eigene SQLite-DB unter `~/.hermes/kanban/boards/<slug>/kanban.db`. Globale Aggregation erfordert Iteration.
4. **`hermes kanban assignees` ist global** (nicht Board-scoped) — zeigt alle Profile aus allen Boards an.
5. **`hermes kanban diagnostics` ist Board-scoped** — zeigt nur Daten des aktuellen Boards.

---

## Skills-Count-Verifikation

```bash
find ~/.hermes/skills/ -maxdepth 2 -name SKILL.md | wc -l
# → 35 lokale Skills

hermes skills list | grep -c enabled
# → 263 (mit builtin + hub + local)

# Skills-Kategorien (top-level):
ls ~/.hermes/skills/ | wc -l
# → 69 Kategorien-Ordner
```

---

## Verifizierte 14 Blocked-Details (für §12.4 Report-Template)

Jeder blocked Task wurde via `hermes kanban diagnostics` und `hermes kanban show <id>` untersucht. Die 3 Failure Modes (A/B/C) sind **empirisch belegt** durch:
- Type A: 3 Tasks mit identischem crash-Muster (pid not alive)
- Type B: 2 Tasks mit identischem protocol_violation Muster (rc=0 ohne kanban_complete)
- Type C: 3 Tasks mit identischem budget_exhausted Muster (80/80 oder 60/60)

Diese Kategorisierung entstand aus der Session und ist in §12.4 als Standard-Triage-Methode dokumentiert.