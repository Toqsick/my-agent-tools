---
name: plan-glm
description: "Use when user asks for a GLM 5.2 implementation plan, invokes `/plan-glm`, or wants a dedicated planner subprocess without changing the current session model. NOT for executing the plan or switching the active session model. Extracts context, spawns GLM 5.2, saves the machine-readable plan, retrieves it, and offers the next step."
version: 1.3.0
author: Yuno
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - planning
    - plan-mode
    - implementation
    - glm
    - subprocess
    related_skills:
    - plan
    - better-plan-strategy
    - subagent-driven-development
    - report-synthesis
    - hermes-agent
lane: koenigin
reasoning_effort: xhigh
trigger_keywords: ['the', 'plan', 'plan-glm', 'glm', 'session']
keywords: ['plan', 'session', 'model', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['hermes-plan-mode-recovery', 'plan', 'plan-review-and-orchestrate']
---

# Plan-GLM: GLM 5.2 Planning Subprocess

Spawn a **dedicated GLM 5.2 process** that writes an implementation plan using
the full `plan` skill methodology. The current session model is NOT changed.

## When to use

- User types `/plan-glm` or asks for a GLM 5.2 plan
- Current session model is NOT GLM 5.2 (e.g. Telegram MiniMax, subagent M3)
- User explicitly asks for a GLM 5.2 plan — honor the request **without offering alternatives or arguing for the current model**. Basti's working-style preference (2026-07-17): *"GLM ist besser im Planen, route zu ihm."* He acknowledges that M3 can also plan but wants GLM's planning depth. Just do it.

If the current session IS already GLM 5.2, consider plain `/plan` instead —
spawning a subprocess adds ~10-30s overhead for no model benefit.

## Core mechanism

A one-shot `hermes chat` process is spawned with:
- Model forced to `glm-5.2` via `-m` flag
- Provider forced to `zai` via `--provider` flag
- The `plan` skill preloaded via `-s plan` **AND** `better-plan-strategy` via `-s better-plan-strategy`
- `--yolo` to prevent approval hangs (planning is read-only + one markdown write)
- `-Q` quiet mode for clean programmatic output

**Warum `better-plan-strategy` als zweiter Skill?** Mass-Audit 2026-07-17:
19/23 Plänen (83%) hatten 0-1 von 6 Quality-Gates. Der Grund war NICHT, dass
`better-plan-strategy` nicht existierte — sondern dass er nie als Prerequisite
geladen wurde. Durch `-s better-plan-strategy` lädt GLM 5.2 automatisch die
S1-S7 Quality-Gate Checklist, ohne dass der Brief sie explizit einfordern muss.
Bewiesen 2026-07-17: Nach Ladung 2 von 2 Plänen mit 100% Gate-Coverage.

The spawned process explores the codebase with full tool access (read_file,
search_files, etc.), then writes the plan to `.hermes/plans/`.

## Workflow

### Step 1: Extract task context

From the current conversation, identify:
- The task/goal to plan (what needs to be built/fixed/refactored)
- Key files, modules, constraints mentioned
- Design decisions or preferences stated
- Current working directory (pass to spawned process)

### Step 2: Write task brief

Write a concise but **self-contained** task brief. The spawned GLM 5.2 process
has ZERO conversation context — it only sees what's in the brief.

Use `write_file` to create `/tmp/plan-glm-brief.md`:

```markdown
# Planning Task

## Goal
[one clear sentence describing what to plan]

## Context
- [key files/modules involved]
- [design decisions or constraints from conversation]
- [relevant background the planner needs]

## Working directory
[current working directory path]

## Additional constraints
- [testing requirements, dependencies, etc.]
```

### Step 3: Spawn GLM 5.2 planner

**Preferred: `terminal` tool directly** (simplest):

```bash
hermes chat -q "$(cat /tmp/plan-glm-brief.md)" \
  -m glm-5.2 \
  --provider zai \
  -s plan \
  -s better-plan-strategy \
  -Q \
  --yolo \
  --max-turns 30
```

Set `timeout=300`. Planning involves codebase exploration.

**Alternative: `execute_code` with subprocess** (for safe string escaping when the brief contains quotes):

```python
import subprocess, json

brief = open("/tmp/plan-glm-brief.md").read()

cmd = [
    "hermes", "chat",
    "-q", brief,
    "-m", "glm-5.2",
    "--provider", "zai",
    "-s", "plan",
    "-s", "better-plan-strategy",
    "-Q", "--yolo",
    "--max-turns", "30"
]

r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
print(r.stdout)
# Plan file is saved to .hermes/plans/ by the spawned process
```

**Background mode (für Pläne > 3 Min)**:
Gleicher Befehl, aber via `terminal(background=true, notify_on_complete=true)` — der User kann weiterarbeiten während GLM plant:

```bash
hermes chat -q "$(cat /tmp/plan-glm-brief.md)" \
  -m glm-5.2 \
  --provider zai \
  -s plan \
  -s better-plan-strategy \
  -Q \
  --yolo \
  --max-turns 30
```

⚠️ **CRITICAL**: Kein `&` anhängen, keine Subshell mit `&& ... &`. Hermes' `background=true` handled das Backgrounding bereits. Ein zusätzliches `&` in der Shell killt den Bash-Wrapper bevor `hermes chat` starten kann. Validierter Fehler 2026-07-17: Erster Versuch mit `&` — Wrapper-PID lief aber `hermes chat` nie (siehe Pitfall "Background-mode doppeltes Backgrounding").

### Step 4: Retrieve and present

The spawned process saves the plan to `.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md`.

1. Parse the plan file path from the process output
2. Read the plan file with `read_file`
3. Present a brief summary to the user with:
   - Plan file path
   - Number of tasks identified
   - Key architectural decisions
   - Estimated complexity

### Step 5: Offer execution

After presenting, offer the execution handoff:

> "Plan ist ready. Soll ich mit `subagent-driven-development` die Tasks
> nacheinander ausführen lassen?"

## Command reference

| Flag | Purpose |
|------|---------|
| `-q "..."` | One-shot non-interactive query (the task brief) |
| `-m glm-5.2` | Force GLM 5.2 model |
| `--provider zai` | Force z.ai provider (GLM API key from .env) |
| `-s plan` + `-s better-plan-strategy` | Preload plan-writing skill AND quality-gate checklist (beide Flags setzen, einzeln oder zusammen) |
| `-Q` | Quiet: suppress banner, spinner, tool previews |
| `--yolo` | Bypass approval prompts (safe: planning is read-only + 1 write) |
| `--max-turns 30` | Allow up to 30 tool-call iterations for codebase exploration |

**GLM-5.2 Reasoning-Auflösung (wichtig fürs Verständnis von `reasoning_effort`).** GLM-5.2 kennt effektiv nur **zwei** Reasoning-Stufen: `_glm_5_2_reasoning_effort` (`plugins/model-providers/zai/__init__.py:62`) mappt `xhigh`/`max`/`ultra` → **`max`** und alles andere Aktive → `high`. Der Frontmatter-Wert `reasoning_effort: xhigh` dieses Skills landet also als **`max`** (Top-Stufe) — mehr geht nicht, feinere Abstufung existiert auf GLM-5.2 nicht. Das ist gewollt (Planen profitiert von maximalem Reasoning), aber erwarte keine Wirkung von Zwischenstufen. (Kontrast: M3 hat auf `anthropic_messages` ein feinkörniges Token-Budget, `ultra`=49152 — andere Mechanik.)

## Pitfalls

- **Zero context**: The spawned process knows NOTHING about the current
  conversation. The brief must be completely self-contained — include all
  relevant file paths, decisions, and constraints.
- **Approval hangs**: Without `--yolo`, the non-interactive process may hang
  on command approval prompts. `--yolo` is safe here because the `plan` skill
  restricts actions to read-only inspection + writing one markdown file.
- **Timeout**: If planning a large codebase, 5 minutes might be tight.
  Increase to `timeout=600` and `--max-turns 45` for complex tasks.
  Use `background=true` with `notify_on_complete=true` for very long plans.
- **execute_code-Timeout-Falle (kritisch)**: Wenn du `execute_code` verwendest
  (die Alternative mit `subprocess.run`), hat das `execute_code`-Tool SELBST
  ein hard cap von **300s** — unabhängig davon ob `subprocess.run(timeout=600)`
  gesetzt ist. Das Script wird bei 300s gekillt. **ABER**: Der `hermes chat`
  Subprozess läuft in einer eigenen Prozessgruppe und ÜBERLEBT trotzdem.
  → **Empfehlung**: Immer zuerst `terminal` versuchen. `execute_code` nur
    wenn der Brief problematische Quotes/Interpolationen enthält.
  → **Post-Timeout-Verifikation**: Nach einem Timeout NICHT einfach aufgeben:
    1. `ps aux | grep "hermes chat"` — lebt der Subprozess noch?
    2. `ls -lat ~/.hermes/plans/` — wurde trotzdem ein Plan geschrieben?
    In der Praxis überlebt der Subprozess und schreibt den Plan fertig.
- **Working directory**: The spawned process inherits the terminal's cwd.
  Ensure the brief mentions the correct project path if different.
- **Model string**: Must be exactly `glm-5.2` (with hyphen). Provider must
  be `zai` (not `z-ai` or `z.ai`).
- **Verify plan saved**: After the process completes, check that a file was
  actually created under `.hermes/plans/`. If not, the process may have
  failed silently — check stderr in the terminal output.
  Ausnahme bei `execute_code`-Timeout: der Plan KANN trotzdem existieren
  — also `ls` checken bevor du den User informierst.
- **Plan assumptions about real system state — verify with live commands (2026-07-16)**: Der GLM 5.2 Planner schreibt einen Plan basierend auf dem Briefing und Codebase-Exploration, aber er KANN das Filesystem nicht immer akkurat abbilden. Validierter Fall 2026-07-16: Der Plan nahm an, `2026-07-15.md` sei HEALTHY und `2026-07-03.md` sei MISSING — beide Annahmen waren falsch. Die echte Vault-Daily hatte leere Sektionen (PARTIAL) und existierende Dateien die fälschlich als gelöscht galten.\n  → **Queen-Pflicht:** Vor Plan-Execution die Plan-Annahmen mit Live-Commands abgleichen (siehe `references/post-plan-queen-verify.md` — 3-Fragen-Regel + strukturierte Checkliste).\n  → **Nur dann** mit dem Plan fortfahren, wenn Annahmen stimmen oder explizit als Risiko akzeptiert.
- **Background-mode doppeltes Backgrounding (2026-07-17)**: Wenn du `terminal(background=true)` nutzt, darf der command KEIN `&` enthalten und keine Subshell mit `&& ... &` verwenden. Hermes backgrounded den Prozess bereits — ein zusätzliches `&` in der Shell killt den Bash-Wrapper bevor `hermes chat` starten kann. Passiert leicht aus Gewohnheit (`cmd &`). Validierter Fall 2026-07-17: Erster Aufruf mit `&` endete als Zombie-Wrapper (PID 180767, `hermes chat` nie gestartet); zweiter Aufruf ohne `&` lief sauber.
  → **Fix:** `terminal(background=true, notify_on_complete=true)` direkt, ohne Shell-`&`.
  → **Verifikation:** Nach dem Start `ps aux | grep "hermes chat"` checken — muss zusätzlich zum terminal-Wrapper laufen.

### Pitfall PLANNING-1 — Plan-Annahmen ohne Live-Verify (= Mini-Pitfall #42)

- **Symptom:** Plan-Brief referenziert Files / Pfade / Annahmen die gestern Abend wahr waren aber heute nicht mehr stimmen. Subagent-Dispatch arbeitet auf Halluzinationen, viel Re-Work.
- **Root Cause:** Plan-GLM hat Zero Conversation-Context, bekommt nur den Brief, und vertraut dem Brief. Mnemosyne-Recall ist semantic — kann Filesystem-Existenz nicht verifizieren.
- **Fix:** Vor jedem Plan-Write (Queen-Phase): `ls -la` / `find` / `read_file` auf JEDEN Pfad der im Plan vorkommt, Resultate als "Realitäts-Status" Tabelle im Plan dokumentieren.
- **Guard:** 3-Fragen-Regel (siehe post-plan-queen-verify.md § Pre-Plan): (1) Existiert das File im aktuellen System? (2) Stimmt Größe/ModTime mit Annahme? (3) Ist Inhalt was Annahme beschreibt? DANN Plan schreiben.

## Further reading (load when relevant)

- **`better-plan-strategy`** — **Automatisch via `-s better-plan-strategy` geladen.** Die S1-S7 Quality-Gate Checklist ist jetzt immer aktiv. Kein manuelles Nachladen nötig.
- **`references/post-plan-queen-verify.md`** — Strukturierte Checkliste (3-Fragen-Regel, Phase 1-4) um Plan-Annahmen gegen Live-Systemstate zu verifizieren, bevor Subagents dispatched werden. Proven 2026-07-16: 5 von 18 Files wären sonst falsch klassifiziert worden.
- **`references/context-budget-discipline.md`** (in `subagent-driven-development`) — Relevant wenn der Plan viele Tasks (>10) hat und der Subagent-Dispatch Context-Degradation riskiert.
- **`glm-plan-m3-execute`** — Full pipeline that packages plan-glm + better-plan-strategy + subagent-driven-development + critic-gate. Nutze diesen Skill statt plan-glm wenn ein Task Planung UND Ausführung braucht.

## Why not delegate_task?

`delegate_task` children inherit the parent session's model — the `model`
parameter is ignored. Since `delegation.model` is pinned to `MiniMax-M3` in
config.yaml, delegate_task CANNOT force GLM 5.2.

The `hermes chat` subprocess is the ONLY way to get a specific model for a
bounded task without changing the session's active model.

## Integration with Telegram

When invoked from Telegram (where the model is typically MiniMax M2.7):

1. The Telegram agent reads this skill
2. Spawns GLM 5.2 locally via terminal
3. GLM 5.2 writes the plan
4. Telegram agent reads the plan file
5. Sends a summary back to the Telegram chat

The plan file is accessible from both Telegram and Desktop since they share
the same filesystem and `.hermes/` directory.
