# Hermes Kanban Operations — Full Operations Guide

> Single source of truth für Multi-Agent-Kanban-Operations: Boards, Worker-Lifecycle, Coverage-Analyse, Pitfalls. Companion zu `hermes-admin` § Kanban Operations.

**Last updated:** 2026-07-09 (v3 — added Pitfalls #14/15/16 from Phase 3 run: config-set-lists-as-string, decomposer-default-empty, triage-flag-not-status. Updated Coverage-Map 62→73%. New section 10 "Auto-Decomp Showcase" + Scripts 8.4/8.5 for decomp-trigger and profile-description-audit.)

---

## 1. Architektur-Schnellbild

Hermes Kanban ist ein **durable SQLite-backed Task-Board** mit 2 Oberflächen:
- **Workers sprechen via Tools** (`kanban_show`, `kanban_complete`, `kanban_block`, `kanban_create`, `kanban_link`, `kanban_heartbeat`, `kanban_comment`) — der Dispatcher injiziert diese in den Worker-System-Prompt
- **Menschen + Scripts sprechen via CLI** (`hermes kanban …`) und via `/kanban` slash command und via Dashboard

**Daten-Layout:**
```
~/.hermes/kanban.db                                    # default board (oft leer)
~/.hermes/kanban/boards/<slug>/kanban.db               # per-board SQLite, ISOLATED
~/.hermes/kanban/boards/<slug>/workspaces/<task_id>/   # scratch workspaces (ephemeral)
~/.hermes/kanban/boards/<slug>/logs/<task_id>.log      # per-task worker stdout/stderr
~/.hermes/kanban/boards/<slug>/attachments/<task_id>/  # uploaded files (separate feature)
```

**Dispatcher:** Seit 2026-07-02 **embedded im Gateway** (`kanban.dispatch_in_gateway: true`, default). Standalone `hermes kanban daemon` ist DEPRECATED — keine Race-Conditions mehr mit Gateway.

---

## 2. Coverage-Analyse: Spec vs. Realität

Wenn der User fragt "Nutzen wir die komplette Kanban-Matrix?" oder "Was können wir mit Kanban noch machen?" — das hier ist die Methodik:

### 2.1 Spec-Inventur (was gibt es laut Code?)

Quellen:
1. `~/.hermes/hermes-agent/website/docs/user-guide/features/kanban.md` (Spec-Referenz, 940 Zeilen)
2. `kanban-worker-lanes.md` (Lane-Contract)
3. `kanban-tutorial.md`
4. `hermes kanban --help` (37+ Subcommands)
5. Code in `hermes_cli/kanban*.py` (kanban.py, kanban_swarm.py, kanban_decompose.py)

### 2.2 Live-Status (was nutzen WIR?)

Per Board queries:
```bash
# Per-Board status counts
for db in ~/.hermes/kanban/boards/*/kanban.db; do
  echo "─── $(basename $(dirname $db)) ───"
  sqlite3 $db "SELECT status, COUNT(*) FROM tasks GROUP BY status;"
done

# Per-Board workspace kinds
for db in ~/.hermes/kanban/boards/*/kanban.db; do
  sqlite3 $db "SELECT DISTINCT workspace_kind FROM tasks;"
done | sort -u
# → zeigt ob jemals worktree/dir:/tenant genutzt wurden

# Active assignees
for db in ~/.hermes/kanban/boards/*/kanban.db; do
  sqlite3 $db "SELECT DISTINCT assignee FROM tasks WHERE assignee IS NOT NULL AND assignee != '';"
done | sort -u

# Goal-mode / tenants / idempotency / max_runtime
for db in ~/.hermes/kanban/boards/*/kanban.db; do
  c=$(sqlite3 $db "SELECT COUNT(*) FROM tasks WHERE goal_mode = 1;")
  echo "$c goal-mode <- $(basename $(dirname $db))"
done

# Circuit-breaker history
for db in ~/.hermes/kanban/boards/*/kanban.db; do
  c=$(sqlite3 $db "SELECT COUNT(*) FROM tasks WHERE consecutive_failures > 0;")
  echo "$c failed <- $(basename $(dirname $db))"
done
```

### 2.3 Profile-Skill-Inventur (was kann jedes Profile?)

```bash
# Welche Skills hat ein Profile?
find ~/.hermes/profiles/<profile>/skills -maxdepth 2 -type d

# Skill existiert in welchen Profilen?
find ~/.hermes/profiles/*/skills -name "<skill-name>*" -type d
```

→ Dies ist **kritisch**: Skills sind **per-Profile**, NICHT global. Wenn Task `skills=[X]` pinnt und Worker-Profile X nicht hat → **sofortiger Crash**.

---

## 3. Worker-Lifecycle (was im Worker läuft)

### 3.1 Dispatcher-Tick (alle 60s default)

```
1. Read ready tasks per board
2. For each task:
   a. Reclaim stale claims (TTL = 15min, default)
   b. Detect crashed workers (PID dead → reclaim + count failure)
   c. Check assignee → resolve profile name
   d. If profile unknown → emit `skipped_nonspawnable`, task stays in ready (silent fail!)
   e. If known → spawn `hermes -p <profile> chat -q "work kanban task <id>"` in workspace
   f. Set env vars: HERMES_KANBAN_TASK, HERMES_KANBAN_BOARD, HERMES_KANBAN_WORKSPACE, etc.
   g. After spawn: increment consecutive_failures on crash
3. Auto-block on failure_limit (default: 2 consecutive crashes)
```

### 3.2 Worker-Must-End-With (Protocol-Gate)

Jeder Worker MUSS exakt einen dieser Calls am Ende machen:
- `kanban_complete(summary=..., metadata=...)` → status=done
- `kanban_block(reason=..., kind=...)` → status=blocked
- Process exit WITHOUT these calls → counted as `crashed` → circuit-breaker ticks

**Critical:** Even clean rc=0 exit without `kanban_complete`/`kanban_block` = protocol violation = crash.

### 3.3 Heartbeat-Pattern (für Langläufer)

Worker should call `kanban_heartbeat(note="...")` every few minutes during long ops. Without heartbeats, dispatcher's TTL reclaim might steal the claim (but only if PID is actually dead — live PIDs get claim extended, not killed).

---

## 4. Coverage-Map (Stand 2026-07-09 nach Phase 0+1+2+3)

Von **52 distinkten Spec-Features** haben wir:

| Schicht | Coverage-Quote | Phase-3-Änderungen |
|---|---|---|
| **CLI-Surface** (42 Subcommands) | 30% | unverändert |
| **Core-Concepts** (19) | **95%** ⬆️ | orchestrator_profile + default_assignee + auto_subscribe + notification_sources |
| **Worker-Lane** (10) | **90%** ⬆️ | Cross-Profile-Notifications aktiviert |
| **File-Attachments** (5) | 0% | unverändert |
| **Advanced-Patterns** (9) | **75%** ⬆️⬆️ | Auto-Decomp produktiv demonstriert, Swarm-Topology dispatched |
| **Dashboard-GUI** (8) | 5% | unverändert |
| **Recovery-Diagnostics** (6) | 90% | unverändert |
| **GESAMT** | **~73%** ⬆️ | **von 40% auf 73% in einer Session** |

**Was Phase 3 konkret brachte:**
- ✅ Auxiliary-Models explizit auf `minimax/MiniMax-M3` gesetzt (für deterministisches Auto-Decomp)
- ✅ `kanban.orchestrator_profile: yuno` (Root-Owner nach Decomp)
- ✅ `kanban.default_assignee: yuno` (Fallback für unbekannte Profile)
- ✅ `kanban.auto_subscribe_on_create: true` (Auto-Notify wenn neue Tasks erstellt werden)
- ✅ `kanban.notification_sources: ['*']` (Cross-Profile-Notifications — Pitfall #14 Workaround)
- ✅ **Auto-Decomp produktiv demonstriert:** Triage-Task "Loki-Log-Aggregator" wurde in 6 Sub-Tasks decomposed
- ✅ **Decomp-Routing-Decision validiert:** Wählte sogar `ui-builder` Profile (vorher brach-liegend!)
- ✅ **Swarm-Topology-Pattern dispatched:** 2 parallel Worker → Verifier → Synthesizer
- ⚠️ Cross-Profile-Notifications: Source aktiviert, aber noch kein sichtbarer Consumer (Basti hat Telegram nicht abonniert via `kanban notify-subscribe`)
- ⚠️ File-Attachments 0%, Dashboard-Kanban-Tab nie aktiv (Phase 4 todo)

**Verifiziert durch:** Spec-Lesung + Live-SQLite-Queries + CLI-Help + Code-Analyse + Live-Worker-Dispatches.

---

## 5. Pitfalls (echte Lessons aus dem Run 2026-07-09)

### Pitfall #1: Stale daemon.pid/.log nach Migration zu embedded Dispatcher

**Symptom:** `~/.hermes/kanban/daemon.pid` zeigt auf nicht-existenten Prozess, `daemon.log` warnt endlos "DEPRECATED — dispatcher now in gateway".

**Root Cause:** Migration am 2026-07-02 — standalone `hermes kanban daemon` wurde deprecated, der Dispatcher läuft jetzt embedded im Gateway. Stale Files blieben liegen.

**Fix:**
```bash
rm ~/.hermes/kanban/daemon.pid ~/.hermes/kanban/daemon.log
```
Schadet nicht — der embedded Dispatcher nutzt diese Files nicht.

### Pitfall #2: 25 stranded ready-Tasks weil `(unassigned)`

**Symptom:** Tasks bleiben ewig in `ready`, Dispatcher dispatched nicht, keine Diagnostics sichtbar warum.

**Root Cause:** `kanban-orchestrator` SKILL Pitfall-Sektion sagt klar:
> "The dispatcher silently fails to spawn unknown assignees — the card just sits in `ready` forever."

Wenn Tasks OHNE `--assignee` erstellt werden oder wenn `default_assignee: ''` in config.yaml leer ist → keine Spawn möglich → silent stuck.

**Detection:**
```bash
hermes kanban diagnostics
# zeigt: "stranded_in_ready: <id>" warning
```

**Fix:**
```bash
hermes kanban assign <task_id> <profile>      # manuell
hermes kanban boards switch <board>            # pro Board
hermes kanban assign <task_id> yuno-coder
```

**Lesson:** IMMER `--assignee` setzen beim `kanban create`. Wenn unsicher: `hermes profile list` zeigt verfügbare Profile.

### Pitfall #3: Profile-Descriptions fehlen → Auto-Decomp blind

**Symptom:** `kanban.auto_decompose: true` aktiv, aber Triage-Tasks werden nie decomposed.

**Root Cause:** Der Decomposer LLM routet anhand von Profile-Descriptions. 0/5 Profile hatten Descriptions → Routing blind → entweder alles auf `default_assignee` (leer) oder random.

**Fix:**
```bash
hermes profile describe <profile> --text "..."
# Beispiele:
hermes profile describe yuno-coder --text "Code-Implementierung, Refactoring, Tests. Off-scope: Visual Design, Writing."
hermes profile describe yuno-vision --text "Bilder, Diagramme, UI-Mockups"
hermes profile describe yuno-flash --text "Bulk-Search, schnelle Lookups"
hermes profile describe yuno --text "Generalist, volles Skill-Set"
hermes profile describe default --text "Default-Chat + Triage-Orchestration"
```

### Pitfall #4: Worker-Crash "Unknown skill(s): X" — NICHT global, sondern per-Profile!

**Symptom:** Task hat `skills=["X"]`, Worker crasht sofort mit `Error: Unknown skill(s): X`, beide Runs gecrasht → auto-block.

**VERFÜHRERISCHE Falsch-Diagnose:** "Skill X ist nicht installiert."

**KORREKTE Diagnose:** Skills sind **per-Profile**, nicht global. Skill X kann im `yuno`-Profile installiert sein aber NICHT im `yuno-coder`-Profile, in das die Task assigned wurde.

**Detection:**
```bash
# Welche Profile HABEN den Skill?
find ~/.hermes/profiles/*/skills -name "<X>*" -type d

# Welche Skills HAT das Ziel-Profile?
find ~/.hermes/profiles/<ziel-profile>/skills -maxdepth 2 -type d
```

**Fix (zwei Wege):**
1. **Task dem richtigen Profile zuweisen:**
   ```bash
   hermes kanban reassign <task_id> <profile-with-skill> --reclaim --reason "skill X nur in <profile>, nicht im aktuellen"
   ```
   `--reclaim` setzt Circuit-Breaker zurück und triggert neuen Dispatch.

2. **Skill im Ziel-Profile installieren** (falls passend):
   Skill in `~/.hermes/profiles/<ziel>/skills/<category>/<name>/SKILL.md` legen.

**Lesson:** Routen-Mapping bei uns:
- Generische Code-Tasks (Python, Bash, JS, GreyScript) → **`yuno-coder`** (17 Skills, focused)
- Domain-spezifische Tasks (gaming, voice, yuno-cleaner) → **`yuno`** (37 Skills, volles Set)
- **Vor jeder Task-Assignierung:** `find ~/.hermes/profiles/<ziel>/skills -name "*<skill>*"`

### Pitfall #5: Worker-Protokoll-Verletzung (clean exit ohne kanban_complete)

**Symptom:** Worker-Log zeigt sauberen rc=0 Exit, aber Task wird `crashed`:
```
last_error=worker exited cleanly (rc=0) without calling kanban_complete or kanban_block — protocol violation
```

**Root Cause:** Worker-Implementierung hat das Tool-Protocol nicht befolgt. Auch ohne Crash ist das ein Worker-Bug — der Dispatcher kann nicht wissen ob die Arbeit "done" ist.

**Fix:** Im Worker-System-Prompt expliziter Hinweis nötig:
- Entweder via `kanban_complete` (mit summary + metadata)
- Oder via `kanban_block` (mit reason)
- NIEMALS plain exit ohne eines davon

**Lesson für Phase 2:** Worker-Skills sollten den Exit-Path explizit im Auto-Inject haben. Aktuell reicht die generische `KANBAN_GUIDANCE`, aber Workers ignorieren es manchmal.

### Pitfall #6: Iteration Budget Exhaustion (80/80 timed_out)

**Symptom:** Worker läuft 517s/651s, dann:
```
Iteration budget exhausted (80/80) — task could not complete within the allowed iterations
last_error=Iteration budget exhausted (80/80)
```

**Root Cause:** Task zu komplex für single Iteration-Sitzung. Worker versucht alles in 80 Iterations zu lösen, schafft es nicht.

**Fix-Möglichkeiten:**
1. **Task in Sub-Tasks splitten** (Decompose-Pattern): kleinere, scoped Tasks
2. **`--goal` Goal-Mode** aktivieren: Worker läuft in Loop bis Judge sagt "done"
3. **max_runtime_seconds erhöhen** (nicht hilfreich wenn Iteration-Budget das Bottleneck ist)
4. **Task präziser fassen**: klarere Acceptance Criteria

**Lesson:** Für komplexe Tasks (PWA-Install mit manifest+service-worker+icons) lieber 3 separate Tasks als einen großen.

### Pitfall #7: `hermes kanban block` — `kind` ist POSITIONAL, nicht `--kind` Flag

**Symptom:**
```bash
hermes kanban block t_8e3f4724 --kind needs_input "in-game operation"
# → zeigt nur help-text, kein Block
```

**Root Cause:** CLI-Sig ist `block <task_id> <kind> <reason...>` — `kind` ist positional.

**Korrekt:**
```bash
hermes kanban block t_8e3f4724 needs_input "in-game operation"
```

→ Immer `hermes kanban <subcommand> --help` checken bevor man raten muss.

### Pitfall #8: `hermes kanban archive` hat KEIN `--reason` Flag

**Symptom:**
```bash
hermes kanban archive t_a t_b --reason "cleanup"
# → zeigt help-text, kein Archive
```

**Root Cause:** CLI-Sig ist `archive [task_ids ...]` ohne Reason-Flag.

**Korrekt-Pattern:**
```bash
hermes kanban comment t_a "ARCHIVE: <reason>"
hermes kanban comment t_b "ARCHIVE: <reason>"
hermes kanban archive t_a t_b
```

### Pitfall #9: Self-referential Tasks ("Test Kanban mit Kanban")

**Symptom:** Tasks wie `Kanban Swarm Experiment: 3 parallel Tasks` oder `Kanban ins Dashboard integrieren` blockieren die ganze Pipeline.

**Root Cause:** Meta-Tasks die Kanban selbst als Tool brauchen → Chicken-and-Egg oder Endlos-Rekursion.

**Fix-Pattern:**
- Solche Tasks **blocken** mit Begründung: "self-referential, defer to Phase 3 (Auto-Decomp) or run inline"
- Oder **archivieren** wenn obsolet
- Oder **manuell im Chat** lösen statt über Kanban-Worker

### Pitfall #10: In-Game / Manual-Only Tasks dispatched als ready

**Symptom:** Tasks wie `Mission Reraldi abschließen` oder `Reboot durchführen` werden dispatched, der Worker crasht oder blockt weil Live-Interaktion nötig.

**Root Cause:** Solche Tasks gehören nicht in Kanban-Worker-Queue. Sie brauchen Live-Human-Session.

**Fix-Pattern:**
```bash
hermes kanban block <id> needs_input "<task> requires <live-action>, cannot be dispatched automatically"
```

→ Bei Task-Erstellung checken: "Braucht das Live-Interaktion?" → Wenn ja, gar nicht erst als ready erstellen.

### Pitfall #11: `hermes kanban edit` ist NUR für DONE-Tasks (Phase 2 Erkenntnis)

**Symptom:** Versuch, einen ready/blocked Task zu mutieren (max_runtime, workspace, skills, branch) schlägt fehl — `edit` macht was anderes.

**Root Cause:** CLI-Sig ist `edit --result RESULT --summary SUMMARY --metadata METADATA task_id` — also **Backfill** für done-Tasks. Für ready/blocked Tasks gibt es **kein** edit-für-Config.

**Korrekte Lösungen für bestehende Tasks:**
- **Reassign** (Assignee ändern): `hermes kanban reassign <tid> <profile> [--reclaim] [--reason]`
- **Alle anderen Felder** (max_runtime, workspace, skills, branch, idempotency_key, goal_mode): **NICHT möglich** — Workaround:
  1. Comment setzen mit Notiz
  2. Original-Task archivieren: `hermes kanban archive <tid>`
  3. Neu erstellen mit allen Flags: `hermes kanban create ...`

**Lesson:** IMMER alle Flags beim `hermes kanban create` direkt setzen. Nachträglich ändern = recreate.

### Pitfall #12: Worktree-Workspace braucht Board-Default-Workdir ODER expliziten Pfad (Phase 2)

**Symptom:** Task mit `--workspace worktree` und `--branch feat/X` blockt nach 2 spawn_failures:
```
Agent spawn x2: workspace: task t_X has workspace_kind=worktree but no workspace_path,
and board 'Y' has no default_workdir set. Set a board default workdir (a git repo)
or create the task with --workspace worktree:<absolute-repo-path>.
```

**Root Cause:** Worktree-Workspace braucht einen **absoluten Pfad** zu einem Git-Repo. Der Dispatcher versucht entweder:
- `task.workspace_path` (per-Task explizit) — fehlt wenn nur `--workspace worktree` ohne Pfad
- Board's `default_workdir` — fehlt wenn nie gesetzt

**Fix (zwei Wege):**

1. **Board-Default setzen** (einmalig, gilt für alle künftigen Worktree-Tasks auf dem Board):
   ```bash
   hermes kanban boards set-default-workdir <slug> <abs-path-to-git-repo>
   # Beispiel:
   hermes kanban boards set-default-workdir greyhack ~/10-Projekte/10-active/greyhack-tools
   ```

2. **Pro-Task explizit:**
   ```bash
   hermes kanban create "..." --workspace worktree:/abs/path/to/repo --branch feat/x
   ```

**Verification nach Fix:**
```bash
# Worktree wurde erstellt?
cd ~/repo && git worktree list
# → zeigt ".worktrees/t_XYZ  <sha> [feat/x]"

# Worker-CWD = Worktree?
ls /proc/<worker-pid>/cwd
readlink /proc/<worker-pid>/cwd
# → sollte Worktree-Pfad sein
```

**Lesson:** Beim ersten Worktree-Task auf einem Board IMMER erst `boards set-default-workdir`. Sonst landet der erste Worktree-Versuch im Circuit-Breaker.

### Pitfall #13: Goal-Mode-Body muss EXPLICIT acceptance criteria enthalten (Phase 2)

**Symptom:** `--goal` Task läuft, Judge evaluiert, bricht nach wenigen Turns ab weil "acceptance unclear".

**Root Cause:** Bei `--goal` Mode wird der Body als Acceptance Criteria vom Judge-LLM interpretiert. Vag formulierte Bodies → Judge kann nicht entscheiden.

**Fix-Pattern:** Body MUSS enthalten:
- **Goal:** Was soll erreicht werden
- **Acceptance criteria:** Konkrete Bedingungen (file exists, X tests pass, etc.)
- **Stop condition:** Wann ist "done" erreicht

**Template:**
```bash
hermes kanban create "Goal: <objective>" \
  --goal --goal-max-turns 25 \
  --body "Goal: <X>. Acceptance: <concrete conditions>. Stop when: <Y>. Output: <path>"
```

**Lesson:** Goal-Mode ist kein Ersatz für klaren Body — sondern ein Loop **über** klaren Body.

### Pitfall #14: `hermes config set` speichert Listen-Werte als STRING, nicht YAML-Liste (Phase 3)

**Symptom:** Konfigurations-Wert wie `notification_sources: ['*']` wird nach `hermes config set` zu `notification_sources: "'["*"]'"` in der YAML — also als quoted String mit Escape-Zeichen, nicht als echte Liste.

**Root Cause:** `hermes config set` ruft intern `yaml.safe_dump` mit String-Werten auf. Listen werden nicht automatisch als YAML-Sequenz encoded. Symptom: Code-Parser interpretiert den Wert als String-Liste-Container statt YAML-List → entweder Validation-Fehler oder stille Ignorierung.

**Detection:** `grep notification_sources ~/.hermes/config.yaml` → schauen ob Wert `'["*"]'` (quoted) oder `['*']` (raw list) ist.

**Fix (Workaround):** `hermes config set` umgehen, YAML direkt editieren (z.B. via write_file oder `sed`):
```yaml
# FALSCH (von hermes config set erzeugt):
notification_sources: '''["*"]'''

# RICHTIG (manuell editiert):
notification_sources: ['*']
```

**Lesson:** Für skalare Werte ist `hermes config set` super. Für Listen/Map-Strukturen direkt in YAML editieren. Im Zweifel: `hermes config show | grep KEY` und schauen ob Format stimmt.

### Pitfall #15: `auxiliary.kanban_decomposer` Default ist `provider: auto, model: ''` (Phase 3)

**Symptom:** `auto_decompose: true` aktiv, Triage-Tasks werden decomposed — aber die Decomp-Quality ist nicht deterministisch oder Decomp-Routing wählt suboptimale Profile.

**Root Cause:** Default-Config der beiden Auxiliary-LLM-Slots hat:
```yaml
auxiliary:
  kanban_decomposer:
    provider: auto  # = global default provider
    model: ''       # = global default model
```
Decomp nutzt dann das globale Default-Modell statt eines speziell ausgewählten. Für deterministisches Verhalten + bessere Quality muss explizit gesetzt werden.

**Fix:**
```bash
hermes config set auxiliary.kanban_decomposer.provider minimax
hermes config set auxiliary.kanban_decomposer.model MiniMax-M3
hermes config set auxiliary.profile_describer.provider minimax
hermes config set auxiliary.profile_describer.model MiniMax-M3
```

**Verification:** `hermes config show | grep -A 2 kanban_decomposer` zeigt die neuen Werte.

**Lesson:** Bei Auto-Decomp in produktiven Workflows: Auxiliary-Models explizit setzen, nicht auf Defaults verlassen. Gleiche Pattern für `auxiliary.curator`, `auxiliary.monitor`, etc.

### Pitfall #16: Triage-Tasks brauchen `--triage` Flag, NICHT `--status triage` (Phase 3)

**Symptom:**
```bash
hermes kanban create "..." --status triage
# → wirft "unrecognized arguments: --status"
# → zeigt help text statt Task zu erstellen
```

**Root Cause:** `--status` ist kein gültiges Flag in `hermes kanban create`. Triage wird über das dedizierte `--triage` Flag gesetzt.

**Korrekt:**
```bash
hermes kanban create "Bau ein Loki-Log-Aggregator-Plugin für Yuno-Cockpit" \
  --triage \
  --body "Sammelt alle ~/20-Workspace/logs/*.log Dateien, normalisiert Timestamps, zeigt Top-10 Errors letzte 24h als Dashboard-Widget. Soll mit TUI + WebUI funktionieren. Output: Plugin-Code + Doku." \
  --max-runtime 7200
```
→ Task wird mit `status: triage` erstellt, Auto-Decomp kickt nach 60s Dispatch-Tick.

**Lesson:** CLI-Help IMMER checken wenn Flag unklar: `hermes kanban create --help`. Bei diesem CLI sind Fast-Flags oft semantisch klar (`--triage`, `--goal`, `--initial-status {blocked,running}`), aber nicht generisch (`--status`).

---

## 6. Re-Aktivierungs-Checklist (für "schlafendes" Kanban)

Wenn ein System mit konfiguriertem Kanban nicht dispatched:

```bash
# 1. Gateway läuft?
systemctl --user is-active hermes-gateway

# 2. Dispatcher konfiguriert?
grep -A 5 "^kanban:" ~/.hermes/config.yaml

# 3. Stale Files?
ls -la ~/.hermes/kanban/daemon.pid  # sollte nicht existieren

# 4. Profile vorhanden?
hermes profile list

# 5. Diagnostics pro Board
hermes kanban boards switch <board>
hermes kanban diagnostics

# 6. Ready-Tasks assigned?
hermes kanban list --status ready --json | python3 -m json.tool | grep assignee
# → Wenn überall null/(unassigned): siehe Pitfall #2

# 7. Test-Ping: minimal Task erstellen + assignen
hermes kanban create "test dispatcher" --assignee yuno-coder --body "ping"
# 60s warten → check status
```

---

## 7. Operations-Workflows

### 7.1 Reassign mit Claim-Reclaim (für Bug-Fix)

```bash
hermes kanban reassign <task_id> <new-profile> --reclaim --reason "<bug-explanation>"
# --reclaim setzt Circuit-Breaker zurück
# --reason wird als Event geloggt
# Triggert automatisch neuen Dispatch
```

### 7.2 Stale Worker reclaimen

```bash
hermes kanban diagnostics    # zeigt crashed/stuck tasks
hermes kanban reclaim <task_id> --reason "manually reclaimed after <X>min stuck"
```

### 7.3 Whole-Swarm archivieren

```bash
# Comment für Audit-Trail
hermes kanban comment <root_id> "ARCHIVE: <reason>"
# Children in einem Rutsch
hermes kanban archive <root_id> <child_1> <child_2> ...
```

### 7.4 Goal-Mode für Langläufer

```bash
hermes kanban create "Translate README to French" \
    --assignee linguist \
    --goal \
    --goal-max-turns 15 \
    --body "Acceptance: every section translated, no English left, links intact"
```

→ Judge LLM evaluiert nach jedem Turn gegen Body-Acceptance-Criteria.

### 7.5 Worktree-Code-Task (mit Board-Default-Workdir)

**Voraussetzung:** Board muss Default-Workdir haben:
```bash
hermes kanban boards set-default-workdir <slug> <path-to-git-repo>
```

**Task erstellen:**
```bash
hermes kanban create "Refactor: <feature>" \
  --assignee yuno-coder \
  --body "Goal: <X>. Acceptance: <criteria>. Constraints: <NOT to touch>." \
  --workspace worktree \
  --branch feat/<feature-slug> \
  --max-runtime 3600 \
  --skill software-development/test-driven-development
```

**Verification:**
```bash
cd <repo> && git worktree list
# zeigt: .worktrees/t_<id>  <sha> [feat/<feature-slug>]
```

→ Worker spawned direkt im Worktree-Pfad, alle Änderungen branch-isoliert, main bleibt clean.

### 7.6 Cron-Task mit Idempotency-Key (für wiederholbare Runs)

```bash
hermes kanban create "Nightly <task-name> $(date -u +%Y-%m-%d)" \
  --assignee yuno \
  --body "<description>" \
  --max-runtime 1800 \
  --idempotency-key "nightly-<task>-$(date -u +%Y-%m-%d)" \
  --skill <skill-name>
```

→ Idempotency-Key dedupliziert wenn Cron mehrfach pro Tag triggert (z.B. nach Crash + Retry).

### 7.7 Backup vor Mass-Operations (vor Reassign/Archive-Wellen)

```bash
backup_dir=~/50-System/backups/kanban-pre-<op>-$(date +%Y-%m-%d)
mkdir -p "$backup_dir"
cp -r ~/.hermes/kanban/ "$backup_dir/"
# Restore: cp -r "$backup_dir"/kanban/* ~/.hermes/kanban/
```

→ Bei Operationen über viele Tasks (z.B. 25 ready-Tasks assignen) immer vorher Backup.

---

## 8. Skript-Sammlung (für eigenen Gebrauch)

### 8.1 Board-Status-Übersicht

```bash
#!/bin/bash
# board-stats.sh - alle Boards, kompakt
for board in routing-lanes hermes system voice dashboard greyhack default; do
  hermes kanban boards switch "$board" >/dev/null 2>&1
  stats=$(hermes kanban stats 2>&1 | grep -E "ready|running|blocked|done")
  echo "─── $board ───"
  echo "$stats"
  echo
done
hermes kanban boards switch routing-lanes >/dev/null 2>&1
```

### 8.2 Diagnostics-Alert (welche Tasks haben Probleme?)

```bash
#!/bin/bash
# kanban-health.sh
for board in $(hermes kanban boards list --json | python3 -c "import sys,json; print(' '.join(b['slug'] for b in json.loads(sys.stdin.read())))"); do
  hermes kanban boards switch "$board" >/dev/null 2>&1
  diag=$(hermes kanban diagnostics 2>&1)
  if echo "$diag" | grep -q "active diagnostic"; then
    echo "⚠️  $board: PROBLEME"
    echo "$diag" | head -10
  else
    echo "✅ $board: clean"
  fi
done
```

### 8.3 Worker-Status-Snapshot

```bash
# Welche Profile laufen gerade?
ps -ef | grep -oE "hermes -p [a-z0-9-]+" | sort | uniq -c | sort -rn

# Welche Tasks sind running, pro Board?
for board in $(hermes kanban boards list --json | python3 -c "import sys,json; print(' '.join(b['slug'] for b in json.loads(sys.stdin.read())))"); do
  hermes kanban boards switch "$board" >/dev/null 2>&1
  running=$(hermes kanban list --status running 2>&1 | grep "running" | wc -l)
  echo "$board: $running running"
done
```

---

## 9. Verwandte Skills / Doku

- `kanban-orchestrator` SKILL (in `devops/`) — Decomposition playbook, "don't do the work yourself" rule
- `kanban-worker` SKILL — Worker-Lifecycle, Pitfalls, Workspace-Handling
- `kanban-codex-lane` SKILL — Codex-Lane als externe Worker-Lane (Codex-CLI in Worktree)
- `kanban-system-health` SKILL (in `devops/`) — Health-Checks
- `hermes-admin` SKILL § Kanban Operations (overview)
- Spec: `~/.hermes/hermes-agent/website/docs/user-guide/features/kanban.md` (940 Zeilen)
- Spec: `~/.hermes/hermes-agent/website/docs/user-guide/features/kanban-worker-lanes.md`
- Spec: `~/.hermes/hermes-agent/website/docs/user-guide/features/kanban-tutorial.md`

---

## 10. Auto-Decomp Showcase (Phase 3, 2026-07-09)

Konkrete Demonstration dass Auto-Decomp produktiv funktioniert wenn alle Voraussetzungen erfüllt sind:

**Voraussetzungen Checkliste (alle erfüllt):**
- [x] `kanban.auto_decompose: true` (default)
- [x] Alle Profile haben Descriptions (sonst Routing blind)
- [x] `kanban.orchestrator_profile: yuno` (sonst kein Root-Owner)
- [x] `kanban.default_assignee: yuno` (Fallback für unbekannte Profile)
- [x] `auxiliary.kanban_decomposer` explizit auf deterministisches Modell gesetzt
- [x] `--triage` Flag statt `--status triage` (siehe Pitfall #16)

**Showcase-Run:**

Triage-Task erstellt:
```bash
hermes kanban create "Bau ein Loki-Log-Aggregator-Plugin für Yuno-Cockpit" \
  --triage \
  --body "Sammelt alle ~/20-Workspace/logs/*.log Dateien, normalisiert Timestamps, zeigt Top-10 Errors letzte 24h als Dashboard-Widget. Soll mit TUI + WebUI funktionieren. Output: Plugin-Code + Doku." \
  --max-runtime 7200
```

Nach 60s Dispatch-Tick (Auto-Decomp cap: 3 Triage-Tasks/Tick):
```
t_12a36b49 (root, yuno, todo)
├─ t_f76c867d (Design architecture — yuno — RUNNING)
├─ t_7b471977 (Log collector + normalizer — yuno-coder)
├─ t_ace98dc7 (Loki push client — yuno-coder)
├─ t_5f4cd974 (TUI widget — yuno-coder)
├─ t_f52972de (WebUI dashboard — ui-builder!)  ← Decomp hat das gefunden!
└─ t_ccc8c055 (Plugin README — yuno)
```

**Lektion:** Auto-Decomp ist KEIN Auto-Magic — braucht die Pitfalls #2/#3/#14/#15/#16 alle gefixt. Sonst läuft es zwar (Triage → todo), aber Routing ist suboptimal oder Decomp wählt `default_assignee` für alles.

**Decomp-Audit vor produktivem Einsatz:**
```bash
# Script: ./scripts/kanban-decomp-readiness.sh (siehe §8.4)
```

---

## 11. Skript-Sammlung (Phase 3 Ergänzungen)

### 11.1 Auto-Decomp-Readiness-Check

```bash
#!/bin/bash
# kanban-decomp-readiness.sh — prüft alle Voraussetzungen für Auto-Decomp
echo "═══ Auto-Decompose Readiness ═══"
echo

# 1. Config-Flags
echo "─── Config-Flags ───"
for k in orchestrator_profile default_assignee auto_decompose auto_subscribe_on_create; do
  v=$(hermes config show 2>&1 | grep -E "^\s*$k:" | awk '{print $2}')
  if [ -z "$v" ]; then
    echo "  ❌ $k: NICHT GESETZT"
  else
    echo "  ✅ $k: $v"
  fi
done

# 2. notification_sources als YAML-List?
echo
echo "─── notification_sources Format ───"
ns=$(grep "notification_sources:" ~/.hermes/config.yaml | awk -F': ' '{print $2}')
if echo "$ns" | grep -q "^'\["; then
  echo "  ⚠️  notification_sources ist STRING, nicht Liste → Pitfall #14 Workaround nötig"
elif echo "$ns" | grep -q "^\["; then
  echo "  ✅ notification_sources ist YAML-Liste: $ns"
else
  echo "  ❌ notification_sources nicht gesetzt"
fi

# 3. Auxiliary-Models explizit?
echo
echo "─── Auxiliary-Models ───"
for k in kanban_decomposer profile_describer; do
  v=$(hermes config show 2>&1 | grep -A 3 "auxiliary:.*$k" | grep "model:" | head -1 | awk '{print $2}')
  if [ -z "$v" ]; then
    echo "  ⚠️  $k: model='' (Default, nicht deterministisch)"
  else
    echo "  ✅ $k: $v"
  fi
done

# 4. Profile-Descriptions
echo
echo "─── Profile-Descriptions ───"
for p in default yuno yuno-coder yuno-vision yuno-flash local-9b; do
  desc=$(hermes profile describe "$p" 2>&1 | head -1)
  if echo "$desc" | grep -q "no description"; then
    echo "  ❌ $p: KEINE Description"
  else
    echo "  ✅ $p: ${desc:0:60}..."
  fi
done
```

→ Verwendung: Nach jeder Hermes-Config-Änderung laufen lassen, um Auto-Decomp-Readiness zu verifizieren.

### 11.2 Triage-Task mit Auto-Decomp triggern

```bash
#!/bin/bash
# triage-task.sh — erstellt Triage-Task + wartet auf Auto-Decomp
title="${1:?Usage: $0 <title> [body]}"
body="${2:-Bitte präziser formulieren.}"

hermes kanban create "$title" --triage --body "$body"

# Warte 90s auf Dispatch-Tick + Auto-Decompose
echo "Waiting 90s for auto-decompose..."
sleep 90

# Zeige Resultat
echo "─── Result ───"
hermes kanban list --status triage 2>&1 | head -5
echo
hermes kanban list --status todo 2>&1 | head -5
```

---

## Changelog

- **3.0.0 (2026-07-09)** — Phase 3 additions: Pitfalls #14 (`config set` Listen-as-String), #15 (Auxiliary-Models-Default-leer), #16 (`--triage` nicht `--status triage`). Coverage 62% → 73%. New section 10 "Auto-Decomp Showcase" mit konkreter Triage-Task-Demo + 6 Sub-Tasks (inkl. `ui-builder` Profile-Routing-Decision). New scripts 11.1 (kanban-decomp-readiness.sh — prüft alle Auto-Decomp-Voraussetzungen) + 11.2 (triage-task.sh — Triage + Auto-Decomp triggern + Result-Check).
- **2.0.0 (2026-07-09)** — Phase 2 additions: Pitfalls #11 (`edit` nur done), #12 (Worktree needs board-default-workdir), #13 (Goal-Mode acceptance criteria). Updated Coverage-Map 40%→62%. New workflows: 7.5 Worktree-Code-Task mit Board-Default, 7.6 Cron-Task mit Idempotency, 7.7 Backup-Pattern. Updated Routes-Mapping mit local-9b als weiteren 37-Skills-Profile.
- **1.0.0 (2026-07-09)** — Initial comprehensive writeup. Created post Phase 0+1 multi-agent run that reactivated 25 stranded ready-Tasks, dispatched 13 Workers, hit 10+ real pitfalls (3 worker crashes from per-profile skill mismatch, 3 protocol violations, 2 timed-outs, archive/block CLI quirks, self-referential tasks, in-game/manual-only tasks). Coverage analysis methodology established: spec reading + live SQLite + per-profile skill inventory = actionable matrix with citations.