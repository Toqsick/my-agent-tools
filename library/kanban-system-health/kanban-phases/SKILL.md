---
name: kanban-phases
title: "Kanban Phases — Cleanup, Assignment, Worker-Maturity, Bienen-Dispatch"
description: "Use when the Kanban needs setup, cleanup, ready-task assignment, worker-maturity flags, advanced patterns (swarm, auto-decomp, notifications), or 2-Wellen Bienen-Dispatch. NOT for live diagnostics (use kanban-diagnostics), pitfall recovery (use kanban-pitfalls), or audit (use kanban-audit). Covers Phase 0-5 + Ready-Task-Klassifizierung (4 Buckets)."
category: kanban-system-health
version: '3.0'
created: '2026-07-23'
author: Yuno (split from kanban-system-health v2.5)
lane: koenigin
agent: universal
trigger_keywords: ['kanban', 'phase 0', 'phase 1', 'cleanup', 'ready-tasks', 'worker-maturity', 'swarm', 'auto-decompose', 'bienen-dispatch', 'notifications']
keywords: ['kanban', 'phase', 'cleanup', 'ready-tasks', 'worker', 'swarm', 'auto-decomp', 'bienen', 'notifications', 'profile-descriptions']
related_skills: ['kanban-diagnostics', 'kanban-pitfalls', 'kanban-audit', 'kanban-orchestrator', 'board-policy']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from kanban-system-health 2026-07-23)'

license: MIT
---

# Kanban Phases — Cleanup, Assignment, Worker-Maturity, Bienen-Dispatch

Kanban Phases — Cleanup, Assignment, Worker-Maturity, Bienen-Dispatch

_Extracted from kanban-system-health v2.5 on 2026-07-23._

## 3. Phase 0+1 — Cleanup & Ready-Task Assignment (bewährte Reihenfolge)


Wenn der User "reaktivieren" / "ready-Tasks hängen" will, diese Schritte in Reihenfolge:

### Phase 0: Cleanup (30 min)

```bash
### Phase 1: Ready-Task Assignment (1-2 Std)

```bash
### Verification Phase 1

```bash
for board in routing-lanes hermes system voice dashboard greyhack; do
  hermes kanban boards switch "$board" >/dev/null 2>&1
  running=$(hermes kanban list --status running 2>&1 | grep -c "running")
  ready=$(hermes kanban list --status ready 2>&1 | grep -c "ready")
  echo "  $board: $running running | $ready ready"
done
## 4. Ready-Task-Klassifizierung (für Cleanup-Entscheidungen)


Nicht alle ready-Tasks sind Kanban-tauglich. Klassifiziere in 4 Buckets:

### Bucket A: Sofort Kanban-ready (echte Code/Skill-Tasks)

- assignee ist eindeutig
- body hat klare Acceptance Criteria
- keine externen Dependencies (Gameplay, Reboot, etc.)

→ **Sofort zuweisen + loslegen lassen.**

### Bucket B: Self-referential / Meta-Tasks (umformulieren oder blocken)

- Beispiele: "Test Kanban mit Kanban", "Integriere Kanban ins Dashboard"
- **Anti-Pattern:** Kanban kann sich nicht selbst dispatchen ohne externen Trigger
- **Fix:** Body umformulieren mit externen Schritten ODER blocken mit Begründung:
  ```bash
  hermes kanban block <id> dependency "self-referential: 'kanban via kanban' is a deadlock pattern"
  ```

### Bucket C: Manuelle Aktion nötig (archivieren oder blocken)

- Reboot erforderlich
- Physisches Gameplay (GreyHack-Missionen)
- GH-Issues closen als 30s-Inline-Job

→ **`hermes kanban block <id> needs_input "<reason>"`** oder **archive mit Comment**.

### Bucket D: Multi-Step-Architecture-Decision (Auto-Decomp nutzen)

- Voice-Pipeline braucht Architektur-Wahl vor Implementierung
- **Auto-Decompose** kann via Triage-Status greifen:
  ```bash
  hermes kanban create "..." --triage --body "..."
  # 60s warten → Auto-Decomp kickt rein, erstellt 3-6 Sub-Tasks
  ```

---

## 5. Phase 2 — Worker-Maturity (Flags die IMMER beim Create gesetzt werden müssen)


**Gelernt 2026-07-09:** `hermes kanban edit` ist **NUR für done-Tasks** (Backfill summary/metadata). Für ready/blocked Tasks geht nur `reassign` — alle anderen Felder (max_runtime, workspace, skills, idempotency_key, branch) sind **nur beim Create setzbar**.

### Die 7 wichtigsten Flags


| Flag | Default | Empfehlung |
|---|---|---|
| `--assignee` | leer | **IMMER setzen** (sonst stranded) |
| `--max-runtime` | 14400 (4h) | **1800-7200** je nach Task |
| `--workspace` | scratch | `worktree` für Code-Tasks |
| `--branch` | keiner | `feat/<name>` oder `wt/<slug>` |
| `--skill` | keiner | nur wenn Skill im Ziel-Profil vorhanden |
| `--idempotency-key` | keiner | bei Cron/Recurring Tasks |
| `--goal` / `--goal-max-turns` | aus / 20 | bei Langläufern (Goal-Mode = Ralph-Loop) |

### 5 Task-Templates


**Template A: Code-Task mit Worktree**
```bash
hermes kanban create "Implement: <feature>" \
  --assignee yuno-coder \
  --body "Goal: <1 sentence>. Acceptance: <criteria>. Constraints: <what NOT to touch>." \
  --workspace worktree \
  --branch feat/<name> \
  --project ~/10-Projekte/10-active/<repo> \
  --max-runtime 3600
```

**Template B: Cron-Job (idempotent)**
```bash
hermes kanban create "Nightly: <task>" \
  --assignee yuno \
  --body "Daily 02:00 cron, see ~/50-System/bin/<script>.sh" \
  --max-runtime 1800 \
  --idempotency-key "nightly-<task>-$(date -u +%Y-%m-%d)" \
  --skill yuno-cleaner
```

**Template C: Langläufer mit Goal-Mode**
```bash
hermes kanban create "Goal: <complex-objective>" \
  --assignee yuno \
  --body "Acceptance: <detailed criteria>. Stop when: <condition>." \
  --goal --goal-max-turns 25 \
  --max-runtime 7200 \
  --workspace worktree \
  --branch goal/<objective-slug>
```

**Template D: Swarm (parallel → verifier → synthesizer)**
```bash
hermes kanban swarm "Goal: <final outcome>" \
  --worker "yuno-flash:Bulk-Search:research/blogwatcher" \
  --worker "yuno-coder:Deep-Analysis:software-development/plan" \
  --verifier yuno-coder \
  --synthesizer yuno \
  --priority 1
```

**Template E: Triage-Task für Auto-Decomp**
```bash
hermes kanban create "<complex goal>" --triage --body "<brief>"
### Pitfalls Phase 2

- **Worktree-Bug:** `--workspace worktree:/abs/pfad` ODER Board-Default-Workdir in Git-Repo
- **`--status triage`** existiert nicht — nutze `--triage` (Flag ohne Wert)
- **`--goal-mode false`** ist kein gültiger Flag — Goal-Mode ist entweder an (--goal) oder aus

---

## 6. Phase 3 — Advanced Patterns (Swarm, Auto-Decomp, Notifications)


### 6.1 Auxiliary-Models setzen


```yaml
### 6.2 Profile-Descriptions (alle 6)


Vor Auto-Decomp aktivieren — sonst ist Decompose-Routing blind.

```bash
for p in default yuno yuno-coder yuno-vision yuno-flash local-9b; do
  hermes profile describe $p --text "<short description>"
done
```

### 6.3 Swarm-Pattern


`hermes kanban swarm` erstellt automatisch eine Topologie:
```
root (mit Goal)
├─ worker 1 (parallel)
├─ worker 2 (parallel)
└─ verifier (wartet auf beide)
   └─ synthesizer (wartet auf verifier)
```

- 2 Worker maximal pro Swarm für Parallel-Throughput
- Verifier gates "code change written → task done"
- Synthesizer braucht Verifier als Parent

### 6.4 Auto-Decompose


```bash
hermes kanban create "Bau komplexes Feature X" --triage --body "..."
### 6.5 Cross-Profile Notifications


```yaml
### 6.6 Goal-Mode


```bash
hermes kanban create "Goal: ..." --goal --goal-max-turns 20
## 7. Phase 4 — File-Attachments, Dashboard-GUI, Polish


### 7.1 File-Attachments (end-to-end verifiziert)


**Storage:** `~/.hermes/kanban/boards/<slug>/attachments/<task_id>/<filename>`
**DB-Tabelle:** `attachments(id, task_id, filename, stored_path, content_type, size, sha256, uploaded_by)`
**Operations:** `add_attachment`, `list_attachments`, `get_attachment`, `delete_attachment`

**End-to-End-Test-Pattern (via `kanban_db` direkt, falls Auth-Block):**
```python
import sqlite3
from hermes_cli import kanban_db

conn = sqlite3.connect("~/.hermes/kanban/boards/<board>/kanban.db")
task_id = kanban_db.create_task(conn, title="...", assignee="yuno", initial_status="blocked")
### 7.2 Hermes Dashboard (Auth-Block bekannt)


> **Hinweis (H-30, 2026-07-20):** Das built-in Dashboard ist **dokumentiert geparkt**. Einzige gepflegte
> Kanban-UI ist `hermes-webui` (`127.0.0.1:8787`) — siehe §15.5.
```


**Versuch 2026-07-09:** `hermes dashboard --port 8789 --no-open --host 127.0.0.1` → alle `/api/` Routen geben 401.

**Bisher probiert ohne Erfolg:**
- Basic-Auth mit scrypt-Hash + `dashboard_auth/basic` Plugin enabled
- `dashboard_auth/nous` disabled
- `--isolated` flag
- Hypothese: Plugin-Loading-Order oder Cache-Issue

**Workaround:** Nutze `hermes serve` (Port 34647) headless API oder Yuno UI (Port 8767).

### 7.3 Workspace GC


```bash
hermes kanban gc  # löscht stale Workspaces älter 30 Tage
```

---

## 8. Phase 5+ — Evolution (Security + Skill-Migration)


### 8.1 Security-Audit (🚨 P0 wenn Live-Tokens gefunden)


**Pattern für read-only Audit:**
```bash
hermes kanban create "Secrets-Audit (read-only)" \
  --assignee yuno-coder \
  --body "Read-only Audit ob ~/.hermes/config.yaml und .env Secrets im Klartext enthalten. KEINE FIXES — nur Report." \
  --max-runtime 900
```

**Bekannte Findings (Biene-6, 2026-07-09):**
- 🚨 CRITICAL: GitHub OAuth PAT hardcoded in `config.yaml` mcp_servers.github.env
- HIGH: Telegram-Bot-Tokens in `.env` Mirrors
- HIGH: GitHub fine-grained PAT in Per-Profile `.env`
- MEDIUM: OpenRouter keys in `local-9b/.env`

**Fix-Pattern:**
1. Token revoken auf github.com/settings/tokens (oder gleichwertig)
2. Aus `config.yaml` entfernen, nur in `.env` speichern
3. Backup-Files säubern (oder rotieren)
4. Re-Audit als Verification-Task

### 8.2 Skill-Migration


**Variante B (empfohlen):**
1. Symlinks für Duplikate: `ln -s ../default/skills yuno-coder/skills` (spart ~21 MB)
2. `yuno-coder` mit echten Coding-Skills ausstatten (12 software-development skills aus yuno)
3. `yuno-vision` mit Vision-Skills
4. `yuno-flash` entrümpeln
5. NEU: `yuno-research` Profil
6. `yunoo` und `ui-builder` cleanup

### 8.3 Profile-Symlinks (21 MB sparen)


```bash
mkdir -p ~/50-System/backups/profiles-pre-symlink-$(date +%Y-%m-%d)
cp -r ~/.hermes/profiles ~/50-System/backups/profiles-pre-symlink-$(date +%Y-%m-%d)/

cd ~/.hermes/profiles
for p in yuno-coder yuno-vision yuno-flash profiles; do
  [ ! -L "$p/skills" ] && rm -rf "$p/skills" && ln -s ../default/skills "$p/skills"
done
```

### 8.4 Memory-Cleanup automatisieren (Cron)


```cron
## 9. 2-Wellen Bienen-Dispatch (Bastis Lieblings-Pattern)


**Pattern:** Bei mehreren unabhängigen Tasks (Audits, Research, Builds) → 2 Wellen à 3 Bienen gleichzeitig = 6 parallel.

**Welle 1 (sofort):**
```bash
for i in 1 2 3; do
  hermes kanban create "Biene-$i: <task>" --assignee yuno-coder \
    --body "..." --max-runtime <time> &
done
wait
```

**Welle 2 (nach kurzem Warten, 5s):**
```bash
for i in 4 5 6; do
  hermes kanban create "Biene-$i: <task>" --assignee yuno-coder \
    --body "..." --max-runtime <time> &
done
wait
```

**Resultat 2026-07-09:** 6 Bienen dispatched, 5/6 laufen sofort, 1 nach 2 Retries (Worktree-Issue).

**Wann nutzen:** Multi-Audit-Szenarien, parallele Research, Smoke-Tests, "ich brauche 5-10 unabhängige Outputs".

---
