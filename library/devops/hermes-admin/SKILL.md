---
name: hermes-admin
description: |
  Use when you need to use the hermes-admin workflow and its documented procedures.
  NOT for unrelated tasks outside the hermes-admin workflow.
  Provides focused guidance for hermes-admin.
version: 1.9.0
author: Hermes Agent (curator consolidation)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - hermes
    - setup
    - configuration
    - gateway
    - telegram
    - discord
    - cron
    - maintenance
    - troubleshooting
    - skills
    related_skills:
    - coding-agents
    - linux-system-maintenance
  metadata-updated: 2026-07-22 - v6 Patterns O/P/Q added to cron-fleet-audit (O CLI-Drift Silent-OK with bare mnemosyne-sleep vs hermes mnemosyne sleep; P DOW x Hour Live-Compute correction 30+ down to 7 Hot-Slots; Q Inventory-Growth and Pinning-Regression Tracking 46.2 percent after Bulk-Kimi-Jobs). 22.07. Audit, 25 Jobs.
lane: worker-heavy
reasoning_effort: xhigh
trigger_keywords: ['hermes', 'admin', 'workflow', 'need', 'documented']
keywords: ['hermes', 'admin', 'workflow', 'need', 'documented']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['voice-clone', 'github-workflow', 'multi-agent-pitfalls-cheatsheet']
---


# Hermes Agent — Administration & Operations

Single umbrella for all Hermes Agent operations: CLI, config, gateway, messaging, cron, maintenance, and skill authoring.

## Quick Start
```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
hermes                    # interactive chat
hermes chat -q "query"   # single query
hermes setup              # setup wizard
hermes model              # change model/provider
hermes doctor             # health check
```

## Key Paths
```
~/.hermes/config.yaml       # Main configuration
~/.hermes/.env              # API keys and secrets
~/.hermes/skills/           # Installed skills
~/.hermes/sessions/         # Session transcripts
~/.hermes/state.db          # Session store (SQLite)
~/.hermes/logs/             # Gateway and error logs
~/.hermes/auth.json         # OAuth tokens
~/.hermes/hermes-agent/     # Source code (if git-installed)
```

## CLI Reference

### Chat
```bash
hermes chat -q "query" -m "model" --provider openrouter
hermes chat --checkpoints  # enable filesystem checkpoints
```

### Configuration
```bash
hermes config              # View config
hermes config edit         # Open in $EDITOR
hermes config set KEY VAL  # Set value (CANONICAL — see Pitfalls below)
hermes config check        # Validate
hermes auth add PROVIDER   # Add credential
hermes auth list           # List credentials
hermes doctor [--fix]      # Health check
```

**Pitfall — Hermes-Guard auf config.yaml:** `patch` und `write_file` auf
`~/.hermes/config.yaml` werden **by design** vom Cross-Profile-Guard geblockt.
Immer `hermes config set <key> <value>` benutzen. Einzige Ausnahme: `hermes config edit`
(öffnet Editor). Siehe `references/web-provider-config.md` unter "Pitfalls" für
Details inkl. Kommentar-Strip-Nebenwirkung.

**Pitfall — `execute_code` blockiert in einigen Kontexten:** Versuche, Python via
`execute_code` auszuführen, das `subprocess`, `write_file`, `patch` oder andere
Tool-Wrapper aufruft, können mit der Nachricht *"BLOCKED: execute_code runs
arbitrary local Python (including subprocess calls that bypass shell-string
approval checks)"* abgelehnt werden. Die Regel ist **nicht auf Cron-Mode beschränkt** —
auch in normalen User-Sessions blockiert die Sandbox. **Fix:** Direkt
`write_file`/`patch`/`terminal` benutzen statt `execute_code` zu wrappen — ist
ohnehin transparenter für Approval-Flows und produziert klarere Error-Messages
bei fehlgeschlagenen Edits. (Observed 2026-07-23 beim Schreiben eines 11 KB
Install-Plans in den Obsidian Vault: `execute_code` blockiert mit "tool_calls_made=0",
`write_file` lief sofort durch und reportete `bytes_written=11628`.)

### Tools & Skills
```bash
hermes tools list          # Show all tools
hermes tools enable NAME   # Enable toolset
hermes skills list         # List skills
hermes skills install ID   # Install from hub
hermes skills update       # Update installed
hermes plugins list        # List bundled/user plugins
hermes plugins enable NAME # Enable a plugin (takes effect next session)
hermes dashboard           # Web UI dashboard (port 9119, local-only)
hermes portal              # Set up Nous Portal (login, model pick, Tool Gateway)
```

### Gateway
```bash
hermes gateway install     # Install as systemd service
hermes gateway start/stop/restart
hermes gateway status
hermes gateway setup       # Interactive platform config (TUI)
```

### Cron Jobs
```bash
hermes cron list
hermes cron create "30m" --name "job" --prompt "..."
hermes cron pause/resume/remove ID
```

### Sessions
```bash
hermes sessions list
hermes sessions export OUT
hermes sessions prune --older-than 30
```

## Config Sections

| Section | Key options |
|---------|-------------|
| `model` | `default`, `provider`, `base_url`, `api_key`, `context_length` |
| `agent` | `max_turns`, `tool_use_enforcement` |
| `terminal` | `backend`, `cwd`, `timeout` |
| `compression` | `enabled`, `threshold`, `target_ratio` |
| `display` | `skin`, `show_reasoning`, `show_cost` |
| `memory` | `memory_enabled`, `user_profile_enabled`, `provider` |
| `security` | `tirith_enabled`, `redact_secrets` |
| `delegation` | `model`, `max_iterations`, `reasoning_effort` |

Full config reference: https://hermes-agent.nousresearch.com/docs/user-guide/configuration

## Skill Lane Creation

Neue Skill-Lanes (Worker-Rollen) können **nur** via `hermes config set` (nicht via `patch`/`write_file`) angelegt werden — die Config ist schreibgeschützt.

→ See [`references/skill-lane-creation.md`](references/skill-lane-creation.md) for full pattern + example.

## Providers (20+)

OpenRouter, Anthropic, Nous Portal, OpenAI Codex, GitHub Copilot, Google Gemini, DeepSeek, xAI, Hugging Face, Z.AI, MiniMax, Kimi, Alibaba, Xiaomi MiMo, Kilo Code, OpenCode Zen/Go, Qwen OAuth, Custom endpoint.

Docs: https://hermes-agent.nousresearch.com/docs/integrations/providers

## Slash Commands (In-Session)

`/new`, `/model [name]`, `/config`, `/tools`, `/skills`, `/cron`, `/gateway`, `/usage`, `/help`.

Full reference: https://hermes-agent.nousresearch.com/docs/reference/slash-commands

## Web UI Dashboard & Portal — Disambiguation

**"Nous Dashboard"** is ambiguous — three things match. Always clarify with the user before acting.

| Term | What it is | Command |
|------|-----------|---------|
| **Web UI Dashboard** | Local browser UI at `127.0.0.1:9119` | `hermes dashboard` (use `terminal(background=true)`) |
| **`nous` Plugin** | Dashboard-Auth plugin for Nous Portal | `hermes plugins enable nous` (lazy — needs `/reset`) |
| **`portal` Command** | Interactive OAuth login wizard | `hermes portal` (`login`, `info`, `status`, `open`, `tools`) |

**Pitfalls:** Never use `nohup &`/`disown`/`setsid` for `hermes dashboard`. Plugin enable is lazy. Dashboard Auth ≠ Provider setup.

→ See [`references/hermes-dashboard-portal.md`](references/hermes-dashboard-portal.md) for full details.

## MCP Server Setup (Docker-based)

```bash
hermes mcp list              # Server anzeigen
hermes mcp test <name>       # Verbindung testen (NICHT Auth)
hermes mcp add <name>        # Hinzufügen
hermes mcp remove <name>     # Entfernen
```

**Key facts:** Tools heißen `mcp_{server}_{tool}`. Token MUSS in `mcp_servers.<name>.env` (nicht nur `.env`). Nach Config-Änderung: Container killen + `/reset`.

→ See [`references/mcp-server-setup.md`](references/mcp-server-setup.md) for full config + troubleshooting.

## MCP Server Setup (uv-tool / stdio — third-party Python CLI mit MCP-Server)

Wenn ein Drittanbieter-Tool seinen **eigenen MCP-Server** als Binary mitliefert und keine Docker-Image-Form erwartet: direkt aus dem uv-tool aufrufen.

→ See [`references/mcp-server-uv-tool-stdio.md`](references/mcp-server-uv-tool-stdio.md) for NotebookLM-Walkthrough mit Verifikationsschritten und Auth-Setup.

## Gateway & Messaging Platforms

### Quick Gateway Reference
```bash
hermes gateway install
yes | hermes gateway install  # non-interactive
systemctl --user restart hermes-gateway.service  # from USER shell only
hermes gateway status
tail -30 ~/.hermes/logs/gateway.log
```

⚠️ **Restart from agent session is blocked** — see [`references/gateway-restart-workarounds.md`](references/gateway-restart-workarounds.md) for proven workarounds.

### DM Authorization
| Method | Config | Best for |
|--------|--------|---------|
| Pairing (default) | Nothing extra | Multi-user, security |
| `dm_policy: open` | `telegram.dm_policy: open` | Personal bot, testing |
| `allowed_chats` | `telegram.allowed_chats: "ID"` | Group filtering |

### Platform Notes
- **Telegram:** `TELEGRAM_HOME_CHANNEL` must be numeric chat ID. `config.yaml` overrides `.env` — but check both for stale values.
- **Discord:** Enable **Message Content Intent** in Developer Portal. Token: `MTkx...abc.def.ghi` (~70 chars).

→ See [`references/hermes-gateway.md`](references/hermes-gateway.md) for full setup. [`references/messaging-gateway-setup.md`](references/messaging-gateway-setup.md) for platform-specific. [`references/troubleshooting.md`](references/troubleshooting.md) for gateway pitfalls.

## Cron Jobs

### Cron Patterns
```bash
# LLM-driven job
hermes cron create "0 9 * * *" --name "daily-briefing" --prompt "..." --skills daily-briefing

# Script-only job (no LLM tokens)
hermes cron create "0 * * * *" --name "health-check" --script health.sh --no-agent --deliver local
```

### Deadline Reminder Sequence

For time-limited user benefits with hard deadlines (token expiries, promotional credits, subscription renewals, billing deadlines, trial ends). Create a sequence of escalating-urgency one-shot cron jobs with full context embedded in each job — no memory dependency across runs.

**Pattern skeleton:**
1. Identify: target user, deadline in their local time, value at stake, concrete action steps
2. Design intervals: T-5d → T-2d → T-12h → T-4h (cadence escalates as deadline approaches)
3. Each job:
   - `deliver=platform:user_id` (Telegram DM, Discord)
   - `model=cost-effective` (MiniMax-M3 for Basti — each run is an independent send, no reasoning overhead)
   - Embed FULL context: deadline, what's at stake, where to spend, links — agent has zero memory of prior conversations
   - Escalate urgency tone per job (informational → urgent → critical)
4. Track job-IDs for possible cancellation if the user acts early

→ **Worked example (Token Cup 2026-07-19 with 4 jobs):** [`references/cron-deadline-sequence.md`](references/cron-deadline-sequence.md)

### Common Cron Issues
| Issue | Fix |
|-------|-----|
| Wrong skill attached | `cronjob(action='update', skills=['correct'])` |
| Delivery fails | Check target exists, gateway running |
| Script not found | MUST be in `~/.hermes/scripts/` |
| 429 rate limits | Gateway down is most common cause — check `systemctl --user is-active hermes-gateway.service` first |
| `web_extract` fails | Set `web.extract_backend: parallel` in config.yaml |
| File-scanning truncation | Batch limit + state file + increase interval |
| **Provider-drift (#44585)** | After global inference config change (new provider or model) ALL previously-created LLM-driven crons fail with spend-protection error. Fix: `cronjob(action='update', job_id=<id>, provider=<p>, model=<m>)` — **beide Felder in derselben Action** (Pinning ist binär, nicht additiv). **Verify-after-fix:** `cronjob(action='get', job_id=<id>)` muss `model` UND `provider` non-null zeigen; leerer Wert = Pinning hat nicht gegriffen (OAuth-Variant-Provider wie `minimax-oauth` wird vom Tool akzeptiert, ist aber ein anderer Billing-Pfad). **Bulk-Recovery + 8 Lessons:** [`references/cron-pinning-recovery.md`](references/cron-pinning-recovery.md) |
| **Script path/env drift** | Script-cron (no_agent=true) references path that no longer exists → script writes ERROR into its log, exits non-zero, produces no Telegram output. Fix: read the script's log, patch the path, re-test with `bash ~/.hermes/scripts/<name>.sh` |
| **Manual-only script registered as cron** | Script was designed for interactive use (prints `manual-only`, exits 0) but registered as cron. Hermes may show `last_status=error` despite exit 0 because script produced no actionable output. Fix: either make script auto-runnable or remove the cron job |
| **Silent-OK (script exits 0 trotz fehlgeschlagener Steps)** | Script-cron zeigt `last_status=ok` + exit 0, aber ALLE Steps fehlschlagen (z.B. `python3: can't open file`). Output-Datei lesen entdeckt es. Zwei Ursachen: (1) Harccoded Pfade zu gelöschtem Skill → Steps laufen ins Leere. (2) **CWD-Interaktion**: cron-scheduler setzt `cwd=str(path.parent)` = `~/.hermes/scripts/`. Wenn das Script `cd scripts/` macht → `.../scripts/`-Doppelung. `cd` zu totem Pfad scheitert lautlos → Steps starten aus falschem CWD. Fix: Script-Refactor (absolute Pfade, cd-Guards) ODER Job pausieren + Grund dokumentieren |
| **Duplicate jobs from repeated register** | Running `register-workflows.sh` twice creates 2-3x identical crons. Fix: add idempotent guard |

### Cron CLI Quirks

- **`hermes cron create` has NO `--model`/`--provider` flag.** Crons are created with current global config model.
- **`hermes cron update` does not exist** — only the tool `cronjob action=update`.
- **`hermes cron list` display bug:** Often shows the wrong provider. The true execution provider is only visible when running `cronjob action=run`.

### Cron Duplicate-Guard Pattern

When a shell script auto-registers workflows, running it twice creates duplicate crons. Use the idempotent guard pattern:

→ See [`references/cron-duplicate-guard-pattern.md`](references/cron-duplicate-guard-pattern.md) for full pattern + dry-run mode + removal guard.

### Cron Workflow Datei-Format

Wenn ein Cron-Job eine `.md`-Workflow-Datei als Prompt-Vorlage nutzt (z.B. Watchdog-Pattern mit Silent-on-Success): Header mit Typ/Zeitpunkt/Modell/Deliver, Ziel, Schritt-für-Schritt-Anweisungen, Pitfalls.

→ See [`references/cron-workflow-format.md`](references/cron-workflow-format.md)

→ See [`references/cron-debug-deepdive.md`](references/cron-debug-deepdive.md) for debug workflow + provider-key health check + config-drift scripts.
→ See [`references/cron-pinning-recovery.md`](references/cron-pinning-recovery.md) for **bulk-recovery** of provider-drifted LLM crons (Category C).

### Cron Error Categories — 4-Category Diagnostic Model

When a cron shows `last_status=error`, classify by its **nature** before digging into logs.

**🔑 Heuristic — "2+ errors → systemic first":** Wenn 2+ Crons gleichzeitig `last_status=error` zeigen (oder das Briefing mehrere Errors meldet), **zuerst nach systemischer Ursache suchen** — nicht jeden einzeln debuggen. Das spart 20-30 Minuten pro Incident.
- LLM-Crons (nicht `no_agent=true`): sofort Category C (provider drift) checken
- Script-Crons (`no_agent=true`): sofort Category A (path drift) checken
- Nur wenn max 1 Cron betroffen oder systemische Ursache ausgeschlossen → individuelle Logs lesen

| Category | Telltale | Where to confirm | Fix |
|----------|----------|------------------|-----|
| **Category A: Script-cron with missing path/env** | Script writes "ERROR" into its own log, exits non-zero, no Telegram delivery. Cron has `no_agent=true`. | Read the script's log file (e.g. `~/.hermes/orchestrator-self-improve.log`). Test-run: `bash ~/.hermes/scripts/<name>.sh` | Patch the broken path in the script or create the missing directory |
| **Category B: Script-cron designed as manual-only** | Script exits 0 and prints "manual-only" / "Skill-Inventur" / "no endpoint". `last_status=error` despite exit 0 — Hermes flags it because script produced no actionable output. | Run the script directly, check stdout. Read the script's header comments — many wrapper scripts say "MANUAL ONLY" | Either (a) remove the cron job, (b) rewrite script to be auto-runnable, or (c) set `HERMES_ENDPOINT` env var |
| **Category C: LLM-driven cron with provider drift** | Explicit `RuntimeError: Skipped to prevent unintended spend` in gateway log (`journalctl` or `gateway.log`). Says `#44585`. Clean error message — Hermes explicitly refused to run. | `journalctl --user -u hermes-gateway --no-pager -n 50 | grep 44585`. Also `cronjob action=list` shows the error. | `cronjob(action='update', job_id=<id>, provider=<p>, model=<m>)` — **8 verifizierte Lessons** in [`references/cron-pinning-recovery.md`](references/cron-pinning-recovery.md) (Pinning-binär, OAuth-Sonderfälle, Mnemosyne-Pin-Cache, Bulk-Pass-Pattern) |
| **Category D: Silent-OK (script with all failing steps, exit 0)** | Script exits 0, `last_status=ok`, but ALL steps fail (e.g. `python3: can't open file`, `ERROR: ... missing`). Meist hardcoded Pfade zu einem gelöschten Skill. Output-Datei im Audit zeigt ⚠/✗ Zeichen trotz grünem Job. | Read actual output file from `~/.hermes/cron/output/<jobid>/latest` — nicht auf `last_status` verlassen. Zeilen auf `Error`, `can't open`, `✗`, `ERROR` scannen. | (a) Patch Script-Pfade (absolute paths statt cd+relativ). (b) Job pausieren + Grund dokumentieren. (c) Job entfernen wenn Pipeline obsolet. Wichtig: **fix erstellen, dann Job wieder aktivieren** — kein Silent-Stale dulden. |

**Diagnostic shortcut:** Find all categories in one command:
```bash
journalctl --user -u hermes-gateway --since "1h" --no-pager | grep -E "error|fail|44585|RuntimeError"
```
Then check the script's log for Category A/B vs gateway log for Category C, and Category D via output-file inspection.

→ Full details with real session examples: [`references/cron-error-categories.md`](references/cron-error-categories.md)

### Cron Fleet Audit — Systematische Flotten-Health-Prüfung

> **Wann:** Periodisch (monatlich), nach Config-Change, nach Skill-Cleanup, post-Incident.
> **Was:** Prüft ALLE Jobs systematisch — nicht nur `last_status`, sondern echte Outputs und Pfade.

4-Phasen-Protokoll:
1. **Baseline** — alle Jobs per `python3 -c "import json; json.load(open('~/.hermes/cron/jobs.json'))['jobs']"` erfassen
2. **Multi-Pass** — `last_status` lesen → Output-Dateien lesen (`~/.hermes/cron/output/<jobid>/latest`) → Dead-Path-Check für Script-Jobs
3. **Gap-Analyse** — gegen 4 Anti-Pattern-Filter (Dead-Path, Silent-OK, Provider-Drift, Manual-Only)
4. **Lane-Overlap & Pinning** — DOW×Hour-Matrix für Schedule-Ballung, Pinning-Quote 100% anstreben

**Entdeckte Anti-Patterns (echte Funde):**
- 🟥 Script-Cron mit `cd "$SKILL_DIR"` zu gelöschtem Skill → Job läuft, aber alle Steps failen
- 🟧 `last_status=ok` obwohl kein Step funktioniert (s.o. Category D)
- 🟧 Stündlicher Job (`0 * * * *`) erzeugt 60+ Lane-Overlaps/Woche

→ Vollständige Methodik mit Python-Code + Report-Format: [`references/cron-fleet-audit.md`](references/cron-fleet-audit.md)

→ **Ausrührbares Audit-Script:** [`scripts/cron-fleet-audit.py`](scripts/cron-fleet-audit.py) — standalone Python, erzeugt strukturierten Markdown-Report. Erkennt Silent-Stale (inkl. Fresh-Schedule-Distinktion), Unpinned Agent-Jobs (ausgeschlossen Script-Mode mit Rest-Provider-Feldern), Schedule-Overlaps. Aufruf: `python3 ~/.hermes/skills/devops/hermes-admin/scripts/cron-fleet-audit.py`

### Deep-Audit Workaround (2-Phase Model-Limit-Pattern)

> **Wann:** Das optimale Modell (Fable 5, Claude Sonnet 4.5, Gemini Pro) ist rate-limited (Pro-OAuth Weekly, API-Quota).
> **Was:** Pre-Audit mit verfügbarem Modell → strukturiertes Briefing → Cron-Job am Reset-Zeitpunkt → Tiefer Audit mit Premium-Modell → Diagnose/Fix-Split.

**Das Pattern (4 Phasen):**

1. **Transparenz** — dem User den Limit-Status zeigen, nicht verheimlichen. Fakten: Reset-Zeit, Workaround-Plan.
2. **Pre-Audit** — Sofort mit dem verfügbaren Modell (MiniMax-M3, DeepSeek, lokal) einen Sweep fahren. Scope-Struktur A–H (siehe unten), read-only Tools. Liefert: grobe Landkarte, schnelle Quick-Wins, Invarianten-Prüfung.
3. **Briefing + Cron** — Strukturiertes Briefing für das Premium-Modell erstellen: Scope, Invariants, Output-Schema, Out-of-Scope, Pre-Audit-Brücke (damit Fable 5 nicht bei Null anfängt). Cron-Job auf Reset-Zeitpunkt + 30 Min setzen mit Telegram-Delivery.
4. **Diagnostiker/Chirurg-Split** — Premium-Modell ist **read-only Diagnostiker** (Reports, keine Edits). Verfügbares Modell ist **Chirurg** (setzt Fixes um nach User-Freigabe). Spart 50% Premium-Token-Kosten.

**Briefing-Struktur (wiederverwendbar):**

| § | Inhalt |
|---|--------|
| 1 | Mission in einem Satz |
| 2 | User-Profil-Snapshot (OS, Hardware, Werte) |
| 3 | Scope-Matrix (A–H: Skills, Crons, Memory, Config, Plugins, Security, Cost, Docs) |
| 4 | Out-of-Scope (hart: keine Edits, keine Destruktion, keine Volltext-Secrets) |
| 5 | Invariants (Reproducibility-First, Severity-ehrlich, konkret, lokal umsetzbar) |
| 6 | Output-Format-Schema (P0–P3 + Positive + Quick-Wins + Tooling-Lücken) |
| 7 | CLI-Aufruf (vorbereitet für Cron) |
| 8 | Pre-Audit-Brücke (was der Vor-Auditor gefunden hat — nicht duplizieren, Widersprüche flaggen als `C-###`) |
| 9 | User-Flow nach Audit (liest → wählt Quick-Wins → delegiert Fixes an *anderes* Modell) |

**Cron-Setup für Deep-Audit:**

```
# 1. Briefing erstellen → ~/.hermes/docus/audits/<topic>-<YYYY-MM-DD>/
# 2. AUDIT_TASK.md: 10-20 Zeilen, reiner Task-Prompt, claude -p kompatibel
# 3. Cron anlegen (via cronjob tool): prompt startet CLI-Befehl für Premium-Modell
```

**Wichtig — Provider-Unterschied:** Der Cron-Job läuft mit einem verfügbaren Provider (z.B. MiniMax-M3). Der Task-Prompt startet dann intern `claude -p "$(cat AUDIT_TASK.md)"` als Bash-Befehl — das ist der **separierte Premium-Modell-Aufruf**. Der Cron-Provider ist nur der Spawner, nicht der Auditor.

**Anti-Patterns:**
- ❌ Premium-Modell für Fixes nach dem Audit einsetzen — ist Diagnostiker, nicht Chirurg
- ❌ Audit-Output als "fertiger Report" ausgeben wenn Tools abgelehnt wurden — lieber ehrlich Report + Workaround
- ❌ Ohne Pre-Audit-Brücke arbeiten — Premium-Modell beginnt dann bei Null statt auf Vorarbeit aufzubauen
- ❌ `workdir` vergessen — dann fehlen die AGENTS.md/CLAUDE.md aus dem User-Home

→ **Vollständiges Beispiel (Fable 5 Hermes-Audit 2026-07-11):** Siehe `~/.hermes/docus/audits/fable5-audit-2026-07-11/` — enthält BRIEFING.md, AUDIT_TASK.md, PRE_AUDIT_FINDINGS.md.

## Post-Update Checklist

After `hermes update`: (1) `hermes tools list` (2) `hermes cron list` (3) `hermes doctor` (4) `hermes status --deep` (5) check venv pip `ls ~/.hermes/hermes-agent/venv/bin/pip*` (6) check provider config wasn't reset.

## Security Hardening
```bash
chmod 600 ~/.hermes/state.db ~/.hermes/kanban.db
chmod 600 ~/.hermes/logs/agent.log ~/.hermes/logs/errors.log
chmod 700 ~/.hermes/state-snapshots/
hermes config set telegram.dm_policy closed
hermes config set security.redact_secrets true
hermes config set session_reset.mode idle
```

## Backup & Restore

**Critical:** NEVER include `.env` or `auth.json` in backups (check `archive/`, `profiles/*/`, `state-snapshots/` too).

Quick core backup: `tar czf ~/backups/hermes-core-$(date +%Y%m%d).tar.gz` with `--exclude` for `hermes-agent/*`, `state.db*`, `.env*`, `cache/*`, `archive/*`, `mnemosyne/models/*`, `runtime/node/*`. Result: ~320 MB (vs 13 GB).

→ See [`references/hermes-backup-restore.md`](references/hermes-backup-restore.md) for 3-tier strategy, full exclude lists, restore procedure.

## Skill Authoring

Two locations: user-local (`~/.hermes/skills/<cat>/<name>/SKILL.md` via `skill_manage`) or in-repo (`$HERMES_REPO/skills/...`). Required frontmatter: `name`, `description` (≤1024 chars), `version`, `author`, `license`, `metadata.hermes.tags`. Target 8-15k chars; split into `references/*.md`.

→ See [`references/hermes-agent-skill-authoring.md`](references/hermes-agent-skill-authoring.md) for full guide. For slimming oversized skills, see the `skill-library-maintenance` skill.

## Daemon-ization Pattern

When a repo ships `ctl.sh start|stop|restart` and you want systemd auto-start + crash recovery: create a mode-600 env file, write a systemd-user unit (`Type=forking` + `PIDFile` + `EnvironmentFile`), enable + start + verify.

→ See [`references/daemon-systemd-pattern.md`](references/daemon-systemd-pattern.md) for full worked example + unit-file template.

## Custom Live Data Dashboard

When you build a **custom Python HTTP server** to serve live Hermes data (dashboard/health/metrics) as a systemd user service.

→ See [`references/custom-live-data-dashboard.md`](references/custom-live-data-dashboard.md) for full architecture, systemd units, pitfalls, and deployment.

## TTS Provider Switch

When user says "Voice umstellen auf <X>": use `hermes config set tts.provider <X>` + provider-specific voice field.

| Provider | Key field |
|----------|-----------|
| `edge` (default) | `tts.edge.voice` |
| `minimax` | `tts.minimax.voice_id` |
| `elevenlabs` | `tts.elevenlabs.voice_id` + `model_id` |
| `openai` | `tts.openai.voice` |
| `gemini` | `tts.gemini.voice` |

→ See [`references/tts-provider-switch.md`](references/tts-provider-switch.md) for full workflow + voice discovery + pitfalls.

## Model/Provider Switch (Main + Subagent)

When the user says "switch to model X" or "set MiniMax M3 as main": use `hermes config set model.provider <X>` + `hermes config set model.default <Y>`.

→ See [`references/model-provider-switch.md`](references/model-provider-switch.md) for subagent model pinning, cache-lag pitfalls, verification workflow, cron provider-drift, and reasoning-effort scoping.

## Fallback Chain (Automatischer Provider-Failover)

When Hermes encounters API errors (429, 500, timeout, auth failure), it can automatically try the next provider in `fallback_providers`. **This is NOT a state machine** — every new agent/session resets `_fallback_index=0`.

Key facts from code-level verification (2026-07-17):
- `try_activate_fallback()` increments `_fallback_index` on PROVIDER FAILURE only — explicit model switches via `/model` go a completely separate path
- `_fallback_index=0` reset in `agent_init.py:1175` on every agent create (`/new`, new cron run, gateway session)
- Three cooldown tiers: 60s for rate-limit/billing, 5s for non-rate-limit exhaustion, none for client errors
- Gateway refreshes the chain live via `_refresh_fallback_model()` — no restart needed for config changes

→ **Full mechanism (code-linked):** [`references/hermes-fallback-chain.md`](references/hermes-fallback-chain.md) — chain resolution, cooldown mechanics, explicit switch vs fallback distinction, cron interaction, verification commands.

## Kanban Operations (Multi-Agent Worker-Board)

Hermes Kanban ist seit 2026-07-02 mit **embedded Dispatcher im Gateway** (kein standalone `hermes kanban daemon` mehr). Tasks werden über 6 Boards (default + benutzerdefinierte) mit per-Profile Worker-Lanes abgewickelt.

**Top Pitfalls (alle aus echten Runs dokumentiert):**
1. **Stale `daemon.pid`** nach Gateway-Migration → `rm ~/.hermes/kanban/daemon.pid ~/.hermes/kanban/daemon.log`
2. **Stranded ready-Tasks** bei `(unassigned)` → Dispatcher silently fails → `hermes kanban diagnostics` + manuell `assign`
3. **Profile-Descriptions fehlen** → Auto-Decomp blind → `hermes profile describe <p> --text "..."`
4. **Worker-Crash "Unknown skill(s)"** ist **PER-PROFILE** (nicht global!) — falsche Diagnose: "Skill nicht installiert". Korrekt: Skills lookup im Worker-Profile. Fix: `hermes kanban reassign <id> <profile-with-skill> --reclaim`
5. **Worker-Protokoll-Verletzung** — clean rc=0 exit ohne `kanban_complete`/`kanban_block` = crash
6. **Iteration Budget (80/80) timed_out** für zu komplexe Tasks → splitten oder Goal-Mode
7. **`hermes kanban block`** — `kind` ist **positional** (`block <id> <kind> <reason>`), kein `--kind` Flag
8. **`hermes kanban archive`** hat kein `--reason` Flag → Comment vorher, dann archive
9. **Self-referential Tasks** ("Test Kanban mit Kanban") → blocken mit Begründung
10. **In-Game/Manual-Only Tasks** dispatched → blocken mit `needs_input` und Begründung
11. **`hermes kanban edit` nur für done-Tasks** (Backfill summary/metadata) — ready/blocked Tasks NICHT editierbar, nur recreate oder reassign
12. **Worktree braucht Board-Default-Workdir** (`hermes kanban boards set-default-workdir <slug> <path>`) ODER expliziten `--workspace worktree:/abs/path`
13. **Goal-Mode Body muss explicit Acceptance Criteria** enthalten — sonst Judge bricht ab
14. **`hermes config set` speichert Listen als String** — `hermes config set kanban.notification_sources '["*"]'` schreibt `'["*"]'` als quoted String, nicht als YAML-List. Für Listen-Werte: `hermes config set` umgehen und YAML direkt editieren. Symptom: Config-YAML-Validierung schlägt fehl oder Wert wird vom Code-Parser als String statt Liste interpretiert
15. **`auxiliary.kanban_decomposer` Default ist `provider: auto, model: ''`** — Auto-Decomp läuft zwar, aber mit dem globalen Default-Modell. Für explizite Kontrolle: `hermes config set auxiliary.kanban_decomposer.provider <provider>` + `hermes config set auxiliary.kanban_decomposer.model <model>`. Gleiches gilt für `auxiliary.profile_describer`. Symptom: Decomp-Quality nicht deterministisch oder Decomp-Routing falsch
16. **Triage-Tasks brauchen `--triage` Flag**, NICHT `--status triage` (existiert nicht!) — Korrekt: `hermes kanban create "..." --triage`. Bei `--status triage` wirft die CLI die Hilfe. Symptom: "unrecognized arguments: --status"

**Coverage-Quote (Stand 2026-07-09 nach Phase 0+1+2+3):** ~73% der 52 Spec-Features aktiv. Phase 1 brachte 40% → 52% (Ready-Tasks assigned, Profile-Descriptions, erste Worker-Runs). Phase 2 brachte 52% → 62% (Worktree-Workspaces, max_runtime, Idempotency-Keys, Goal-Mode, Board-Defaults). Phase 3 brachte 62% → 73% (Auxiliary-Models explizit auf minimax/MiniMax-M3 gesetzt, orchestrator_profile=yuno, default_assignee=yuno, auto_subscribe_on_create=true, notification_sources=['*'], **Auto-Decomp produktiv demonstriert**: Triage-Task wurde automatisch in 6 Sub-Tasks zerlegt inkl. Routing auf `ui-builder` Profile das vorher brach lag). Hauptdefizite: File-Attachments 0%, Dashboard-Kanban-Tab nie aktiv, Cross-Profile-Notifications noch ohne sichtbaren Consumer.

**Routen-Mapping (verifiziert 2026-07-09 Phase 0+1+2):**
- Generische Code-Tasks (Python, Bash, JS, GreyScript) → **`yuno-coder`** (17 Skills, focused)
- Domain-spezifische Tasks (gaming, voice, yuno-cleaner) → **`yuno`** (37 Skills, volles Set)
- Auch **`local-9b`** hat 37 Skills (volles Set) — gut für lokale Inferenz-Tasks
- Schnelle Lookups → **`yuno-flash`** (step-3.7-flash, 17 Skills)
- Visuelle Inhalte → **`yuno-vision`** (17 Skills)
- **`default`** hat 0 Skills — NICHT für Worker, nur für Chatsitzung/Decompose
- **Vor jeder Task-Assignierung:** `find ~/.hermes/profiles/<ziel>/skills -name "*<skill>*"`

**Pattern:** Jeder globale Provider/Model-Change betrifft ALLE existierenden LLM-Crons. Ein Batch-Update aller unpinned LLM-Crons nach einem Provider-Wechsel ist empfehlenswert.

---

## Category D: Silent-OK — script exits 0 trotz fehlgeschlagener aller Steps

**Session:** `orch-weekly-pipeline` (cron `eef0630309b9`, Sonntag 05:00, no_agent=true)

**Symptom:** `last_status=ok`, letzter Run liefert eine Telegram-Nachricht. Aber die Output-Datei zeigt, dass ALLE funktionalen Steps fehlschlagen.

**Zwei identifizierte Root-Causes:**

### RC1: Dead Skill Path (ursprünglich dokumentiert)

Das Skript `orchestrator-weekly-pipeline.sh` hardcodiert:
```bash
SKILL_DIR="${SKILL_DIR:-/home/bratan/.hermes/skills/orchestration/hermes-orchestration}"
```
und macht `cd "$SKILL_DIR"`, dann `python3 scripts/heuristic_extractor.py`. Der gesamte Skill `hermes-orchestration` wurde gelöscht. Das Skript läuft:
```
cd /home/bratan/.hermes/skills/orchestration/hermes-orchestration  → (toter Pfad, cd scheitert lautlos)
python3 scripts/heuristic_extractor.py → "python3: can't open file 'scripts/heuristic_extractor.py'"
```

### RC2: CWD-Interaktion mit cron-scheduler (neu 2026-07-14)

**Entdeckt in Run #3.** Der cron-scheduler führt no_agent-Scripts mit `cwd=str(path.parent)` aus, d.h. CWD = `~/.hermes/scripts/`. Wenn das archivierte Script selbst `cd scripts/` macht (z.B. aus einem früheren SKILL_DIR-Kontext), entsteht:
```
cron-scheduler cwd       = ~/.hermes/scripts/
Script: cd "$SKILL_DIR" → (toter Pfad, cd scheitert lautlos, bleibt in ~/.hermes/scripts/)
Script: python3 scripts/heuristic_extractor.py 
       → sucht in ~/.hermes/scripts/heuristic_extractor.py  ✗
```

**Doppel-Pfad:` scripts/` ist kein Tippfehler, sondern genau diese Kettenwirkung.** Das archivierte weekly-pipeline.sh (jetzt unter `archive-2026-07-13/`) hatte `cd "$SKILL_DIR"` + `python3 scripts/*.py`. Nach Skill-Löschung fiel `cd` auf CWD zurück — und der CWD war bereits `~/.hermes/scripts/`.

**Lösung (angewandt im Refactor 2026-07-13):** Neues `orchestrator-pipeline.sh` mit `--mode weekly` Flag, absoluten Pfaden, keinem `cd`. Dry-Run verifiziert, nächster Live-Run So 19.07.

---

Das Skript behandelt jeden Fehler als `⚠` (Warning, nicht `✗`/Exit), so dass es am Ende **`exit 0`** erreicht:

```
[2026-07-08 18:49:26] --- Step 0: Heuristic Extractor ---
python3: can't open file '.../scripts/heuristic_extractor.py': [Errno 2] No such file or directory
⚠ Heuristic extraction had issues (see log)
[2026-07-08 18:49:26] --- Step 1: Heuristic Aggregator ---
python3: can't open file '.../scripts/heuristic_aggregator.py': No such file or directory
✗ Heuristic promotion failed
[2026-07-08 18:49:26] --- Step 2: Mnemosyne Import ---
python3: can't open file '.../scripts/mnemosyne_importer.py': No such file or directory
⚠ Mnemosyne import had issues (see log)
[2026-07-08 18:49:26] --- Step 4: Memory Stats --- (dieser liest direkt aus der DB, das klappt noch)
[2026-07-08 18:49:27] === Weekly Pipeline Complete ===  (exit 0)
```

**Schlüsselproblem:** Step 4 (Memory-Stats) funktioniert noch — das ist eine statische DB-Abfrage ohne Skill-Pfad. Das täuscht dem Skript vor, dass "was Sinnvolles passiert ist". Tatsächlich sind die Lern-Schritte 0-3 seit 3+ Wochen tot.

**Diagnose:**
1. Output-Datei lesen (nicht `last_status` trauen):
   ```bash
   ls -t ~/.hermes/cron/output/eef0630309b9/ | head -1 | xargs -I{} cat ~/.hermes/cron/output/eef0630309b9/{}
   ```
2. Nach `python3: can't open` oder `✗` / `⚠` scannen
3. Scripts Pfade mit `bash -x` testen: `bash -x ~/.hermes/scripts/orchestrator-weekly-pipeline.sh 2>&1 | head -30`

**Fix:** Drei Optionen — aufsteigend nach Aufwand:
- A) Job pausieren + Grund dokumentieren (schnellster Weg, stoppt Noise)
- B) `SKILL_DIR` im Script auf existierenden Pfad patchen
- C) Skill `hermes-orchestration` aus Backup (`~/30-Library/hermes-v7/.hermes/skills/orchestration/hermes-orchestration/`) zurückspielen inkl. `memory/runs/`

**Pattern:** Jeder no_agent-Cron mit `cd` + relativen Pfaden ist anfällig für Silent-OK nach Skill-Migration oder Cleanup. Robustere Variante: absolute Pfade in den Python-Calls, oder `cd && pwd || exit 1` Guard einbauen.

**Verwandtes Problem:** Der `orchestrator-weekly-improve` Job (cron `b1381735ce35`) hat DENSELBEN Skill-Pfad, aber seine `last_status=error` ist ehrlich — weil sein `RUNS_DIR`-Check vor Step 0 fehlschlägt und das Script `exit 1` macht. Der Pipeline-Job dagegen hat **Step 4 als Rettungsanker** der ihn exit 0 erreichen lässt.

---

## Quick Reference: Find All Errors in One Command

Wenn Basti fragt „Geht SSH zu meiner Cloud-Instanz?" — Antwort hängt von der **Hosting-Architektur** ab.

- [`references/cloud-connectivity.md`](references/cloud-connectivity.md) — SSH diagnosis, workarounds, hardening, and report template.
- [`references/kanban-operations.md`](references/kanban-operations.md) — Kanban Multi-Agent-Board: Architecture, Coverage-Map, 10 Pitfalls, Re-Activation-Checklist, Operations-Skripts (added 2026-07-09, post Phase 0+1 multi-agent run)
- [`references/cloud-git-sync.md`](references/cloud-git-sync.md) — Git-based sync for Cloud Pods (no SSH/VPN)

## Troubleshooting Quick Reference

- **Voice:** Check `stt.enabled`, install deps in venv, check mic, `/restart` gateway → [`references/troubleshooting.md`](references/troubleshooting.md)
- **Tool not available:** `hermes tools`, `/reset` after enabling
- **Model/provider:** `hermes doctor`, `hermes auth`, check `.env`
- **Gateway crash loop:** `systemctl --user reset-failed hermes-gateway`
- **Changes not taking effect:** `/reset` (tools/skills), gateway restart (config)
- **Ambiguous skill name:** Use fully-qualified path: `skill_view(name='devops/hermes-admin')`
- **Cron provider-drift (Category C):** `cronjob action=get` zeigt model/provider null → [`references/cron-pinning-recovery.md`](references/cron-pinning-recovery.md) Bulk-Pattern

→ [`references/troubleshooting.md`](references/troubleshooting.md) for full deep-dives including 8 gateway pitfalls.

## References

- [`references/hermes-gateway.md`](references/hermes-gateway.md) — Gateway setup, DM auth, platform config
- [`references/messaging-gateway-setup.md`](references/messaging-gateway-setup.md) — Platform-specific setup
- [`references/hermes-config-validation.md`](references/hermes-config-validation.md) — Config validation, version-drift check
- [`references/hermes-maintenance.md`](references/hermes-maintenance.md) — Post-update checks, CLI quirks, provider security
- [`references/hermes-backup-restore.md`](references/hermes-backup-restore.md) — 3-tier backup/restore strategy
- [`references/hermes-agent-skill-authoring.md`](references/hermes-agent-skill-authoring.md) — Skill authoring guide
- [`references/mcp-server-setup.md`](references/mcp-server-setup.md) — MCP Server Docker setup + troubleshooting
- [`references/mcp-server-uv-tool-stdio.md`](references/mcp-server-uv-tool-stdio.md) — MCP Server via uv-tool + stdio
- [`references/daemon-systemd-pattern.md`](references/daemon-systemd-pattern.md) — Daemon-ization: ctl.sh + systemd
- [`references/tts-provider-switch.md`](references/tts-provider-switch.md) — TTS provider switch + voice discovery
- [`references/model-provider-switch.md`](references/model-provider-switch.md) — Model/provider switch + subagent cache-lag pitfall
- [`references/troubleshooting.md`](references/troubleshooting.md) — Troubleshooting deep-dives + gateway pitfalls
- [`references/cron-debug-deepdive.md`](references/cron-debug-deepdive.md) — Cron debug + provider-key health check
- [`references/cron-error-categories.md`](references/cron-error-categories.md) — 4-category model: script-path drift, manual-only script, provider drift, silent-ok
- **`references/cron-fleet-audit.md`** (added 2026-07-11, v2 2026-07-15, v3 2026-07-16) — Systematic fleet health check with temporal pinning-quote drift tracking, **10 extended detection patterns (v3):** Patterns H/I/J — temporal pinning drift, script-mode config garbage, lane-congestion events + Never-Run 3-subclass refinement. Report format with temporal KPI. v2: 7 patterns: @reboot-daemon, comment-schedule-drift, Docker-container-dependency, log-path-persistence, lock-coverage-gap, duplicated-subroutine, missing-log-classification.
- **`references/cron-pinning-recovery.md`** (added 2026-07-10) — Bulk-recovery workflow for Category C with 8 lessons learned + OAuth-Sonderfälle + Mnemosyne-Pin-Audit-Cache
- [`references/cron-debug-notes.md`](references/cron-debug-notes.md) — Prior cron debug session notes
- [`references/cron-truncation-patterns.md`](references/cron-truncation-patterns.md) — File-scanning cron truncation patterns
- [`references/cron-workflow-format.md`](references/cron-workflow-format.md) — Cron workflow .md file format
- [`references/skill-lane-creation.md`](references/skill-lane-creation.md) — Skill lane creation via hermes config set
- [`references/gateway-restart-workarounds.md`](references/gateway-restart-workarounds.md) — Gateway restart workarounds (blocked from agent)
- [`references/custom-live-data-dashboard.md`](references/custom-live-data-dashboard.md) — Custom live Hermes data dashboard architecture
- [`references/hermesultracode-plugin.md`](references/hermesultracode-plugin.md) — Third-party plugin install example
- [`references/hermes-dashboard-portal.md`](references/hermes-dashboard-portal.md) — Dashboard vs. `nous` plugin vs. `portal`
- [`references/js-unicode-key-silent-crash.md`](references/js-unicode-key-silent-crash.md) — V8 silent crash from Unicode object keys in JS
- [`references/cloud-connectivity.md`](references/cloud-connectivity.md) — SSH diagnosis, workarounds, hardening, and report template.
- [`references/kanban-operations.md`](references/kanban-operations.md) — Kanban Multi-Agent-Board: Architecture, Coverage-Map, 10 Pitfalls, Re-Activation-Checklist, Operations-Skripts (added 2026-07-09, post Phase 0+1 multi-agent run)
- [`references/cloud-git-sync.md`](references/cloud-git-sync.md) — Git-based sync for Cloud Pods (no SSH/VPN)
