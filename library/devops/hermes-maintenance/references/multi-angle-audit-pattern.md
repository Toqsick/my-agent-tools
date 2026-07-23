# Multi-Angle Audit Pattern (Tools + System + Security)

**Source:** 2026-06-08 Hermes Tool Integration Audit (Basti: "überprüfe die
gesamte hermes tool integration und gleiche sie mit der doku, den skills und
commands ab. teste und fixe fehler")

This is the **broad** audit pattern — use it when Basti asks for a full
audit/health-check of Hermes itself (not just one area). The 2026-06-06
single-area audit (infra + messaging + gateway) is documented in
`health-audit-2026-06-06.md`; this is the multi-angle version.

## When to use

- "Audit Hermes tool integration"
- "Bug Search & Fix" on the whole Hermes setup
- "Post-update hardening review"
- "Why is X broken, find all the issues"
- After `hermes update` AND a feeling that "more than just the update broke"

## The 5-Phase Pattern

### Phase 0: Sondierung (10-15 min, NO subagents)

Use `execute_code` with Python + `terminal()` for a wide net, not subagents.
Subagents don't know what's interesting yet.

```python
# Pseudo-checklist
1. hermes config                          # current model, provider, config version
2. hermes tools list                      # 25 enabled? any missing?
3. hermes skills list | wc -l             # count skills
4. find ~/.hermes/skills -name SKILL.md | wc -l  # ground truth
5. hermes profile list                    # how many profiles
6. hermes cron list                       # all 11 jobs
7. systemctl --user list-units --type=service --state=running | head -20
8. df -h / ; du -sh ~/.hermes/*           # disk
9. tail -50 ~/.hermes/logs/errors.log     # latest errors
10. grep -rE '...' ~/.hermes/skills/ | head  # skill consistency
```

**Key insight:** Do NOT skip Phase 0. Subagents starting without this
context produce 30+ tool calls of fumbling. Phase 0 gives you a precise
briefing to give them.

### Phase 1: 3 Parallel Subagents (5-10 min wall time)

Spawn exactly 3 subagents in parallel (Pitfall: 4+ = coordination overhead
exceeds value). Each gets `terminal, file` toolsets (no `web` — we want
**measurements, not estimates**).

**Scope division (proven, 2026-06-08):**

| Expert | Scope | Key questions |
|--------|-------|---------------|
| **E1: Tool-Architect** | Hermes CLI, profiles, skills, plugins, gateway, toolsets | Does `hermes config` show what we expect? Do all subcommands work? Are skills installable? |
| **E2: Infra-Engineer** | Crons, user services, logs, system resources, errors.log, disk | Do all cron-referenced scripts exist? Are logs too permissive? Is anything world-readable? |
| **E3: Security-Hardener** | Config files, .env, state.db, scripts/, .git/ in profiles, auth.json, gateway permissions | Are secrets protected? Are tokens valid format (Pitfall 16)? Are there stale config files? |

**Briefing template (every subagent gets this):**

```
SYSTEM: [OS, hardware, user]
AKTUELLER STATE: [exact output of Phase 0]
NEU SEIT LETZTER SESSION: [what changed]
AUFGABE: [8-12 concrete questions, numbered]
TRENNUNG: [Sofort umsetzbar (<30 Min) vs Großprojekt]
OUTPUT: [explicit path, e.g. /tmp/research-e1-tool-integration.md]

WICHTIG: 
- Bei großen Outputs (>100 Zeilen): head/tail/wc/grep
- MAX 30 tool calls
- NUR MESSEN, NICHT SCHÄTZEN
- Datum-Filter bei "ERROR flutet" Claims (Pitfall 26)
```

### Phase 2: Sofort-Fixes (parallel zu Phase 1, ~5-10 min)

While subagents run, parent does the obvious quick wins:

- Re-enable deactivated toolsets (e.g. `hermes tools enable browser`)
- Fix obvious permission issues (chmod 600 on world-readable secrets)
- Clear caches (`npm cache clean --force`, `pip cache purge`, `uv cache clean`)
- Verify pending fixes from prior sessions
- Run `hermes doctor` and `hermes status --all`

**Pitfall 14 (NEVER sed on .env):** Use Python string manipulation
or `patch()` tool for .env edits. Always backup first:
```bash
cp ~/.hermes/.env ~/.hermes/.env.pre-<fix-name>-$(date +%s)
```

### Phase 3: Synthese + VERIFY subagent claims (10-15 min)

**Critical: verify every "✅ done" claim.** Subagent-Self-Reports sind NICHT
Fakten (Pitfall 5). Common verification patterns:

| Claim type | How to verify |
|------------|---------------|
| "I changed X" | `read_file` or `grep` the file to see the new state |
| "Service is running" | `systemctl --user status <svc>` — check Main PID + Tasks, NOT just is-active (Pitfall 22) |
| "Fixed permissions" | `stat -c '%a %n' <file>` |
| "X errors in log" | `grep <error> log | awk '{print $1}' | sort -u | tail -10` — DATE FILTER (Pitfall 26) |
| "Model loads" | `curl -s /api/ps | jq '.models[]'` — actual VRAM + ctx, not just "loaded" |
| "Skill updated" | `hermes skills list | grep <name>` — check Status column |

**Pitfall 26 in action (2026-06-08):** Subagent E2 reported
"~400× @OlympAgentBot ERROR flutet errors.log — Chat-ID als @-Handle
statt numerisch." Factually true (400+ matches in log), but ALL errors
were from 2026-06-02 to 2026-06-04. The bug had been fixed in a later
update; 4 days error-free. No action needed. **Caught only because
parent filtered by date.**

### Phase 4: Execute P0 + Doku

After verification, execute P0 fixes in dependency order. For each:
1. Apply fix
2. Verify (status check, re-grep, etc.)
3. Document in `~/docs/system/hermes-<scope>-audit-YYYY-MM-DD.md`

Doku structure (proven template):

```markdown
# [Title] Audit — YYYY-MM-DD

**Datum:** YYYY-MM-DD
**Anlass:** [Was triggered this audit]
**Methode:** Multi-Angle Audit Pattern (Phase 0-5)
**Hermes Version:** X.Y.Z

## Executive Summary
[1-2 sentences: total fixes applied, P0/P1/P2 counts, phantom bugs caught]

## Sofort-Fixes (N applied)
| # | Fix | Befehl | Status |

## Research-Ergebnisse
### Expert E1: [scope]
- Key finding 1
- Key finding 2

### Expert E2: [scope]
...

### Expert E3: [scope]
...

## P1-Befunde (dokumentiert, deferred)
[Items needing user decision or >30 min work]

## P2-Befunde (informativ)
[Nice-to-know items, no action]

## Phantom-Bugs (Subagent-Confabulationen entlarvt)
[Cases where subagent reported active issues that were actually
historical or already fixed]

## Pitfall-Compliance Checklist
[13-15 pitfall checks with ✅/❌]

## Dateien & Pfade
### Geänderte Files
### Backups
### Subagent-Reports

## Retrospektive
### Was funktionierte
### Was nicht optimal lief
### Lessons Learned
```

### Phase 5: Retrospektive + Skill/Memory updates

After the audit, identify reusable patterns:
- New gotchas → patch `hermes-maintenance` skill
- New pitfall numbers → add to `multi-agent-research` skill
- New user preferences → memory
- Repeated workflow → consider new umbrella skill

## 2026-06-08 Audit — Concrete Findings

### Befunde (P0, alle gefixt)

1. **gmail-organizer-cron Symlink fehlte** — Script lag in `~/bin/`,
   Cron erwartet `~/.hermes/scripts/`. Fix: `ln -sf ~/bin/<name> ~/.hermes/scripts/`
2. **Snapshot `state.db` 644 (world-readable!)** — Hermes Update repariert
   permissions NICHT. **Manuell nach jedem Update prüfen:**
   ```bash
   find ~/.hermes/state-snapshots -type f -exec chmod 600 {} \;
   find ~/.hermes/state-snapshots -type d -exec chmod 700 {} \;
   ```
3. **Scripts 711 (world-executable) statt 700** — Default nach `hermes update`
   ist 711. Für Cron OK, 700 ist sicherer. Fix: `chmod 700 ~/.hermes/scripts/*`
4. **ANTHROPIC_TOKEN in .env war falsch** — war `sk-nous-...` (Nous-Portal Token
   mit falschem Key-Namen). **Hermes cleared ANTHROPIC_TOKEN automatisch seit
   v9** (siehe `hermes_cli/config.py: v8→9 migration`). Falls vorhanden, ist
   er Konfig-Schmutz — User fragen ob clearen.
5. **`shell-hooks-allowlist.json` fehlte** — Gateway-Hooks laufen ohne
   Einschränkung. Fix: `echo '{"hooks": {}}' > ~/.hermes/shell-hooks-allowlist.json`
6. **`computer_use` Toolset enabled auf Linux** — Toolset ist macOS-only.
   Fix: `hermes tools disable computer_use`
7. **Cache: 2.2GB freigegeben** (npm 1.1G, pip 541M, uv 650M)
8. **baoyu-article-illustrator outdated** — `hermes skills update <name>`

### P1 (dokumentiert, teils umgesetzt)

- `state.db` 112MB prune >30 Tage (50-70MB freigebbar)
- `state-snapshots` 110MB alt (nach erfolgreichem Test löschen)
- Logs 644 (world-readable) — `chmod 640`
- godmode scripts 664 — `chmod 600`
- 5 stale linked_files zu externen Auth-Files (Codex, Notion, Google)
- `hermes-patch-restore` Cron `deliver: telegram` ohne ID

### P2 (informativ)

- Hermes Doctor zählt Profile falsch (1 statt 2)
- Skills count diff (120 listed vs 125 files) — Counter-Inkonsistenz
- OpenRouter 3500× WARNING (payment/credit) — Bekannt, graceful skip
- Telegram Fallback-IP 149.154.166.110 — stabil über Fallback
- CLI Singular/Plural-Inkonsistenz (`hermes cron` singular geht,
  `hermes skill/tool/plugin` singular gehen NICHT) — UX-Bug, source patch nötig

### Phantom-Bugs entlarvt (Pitfall 26)

- **@OlympAgentBot 400+ errors** → alle von 02.-04.06., seither 4 Tage behoben
- **local-9b TIMEOUT 30s** → Subagent-Claim, Realität antwortet in 57s

## Wann NICHT diese Pattern verwenden

- **Single area** (z.B. nur "warum crasht der Gateway") → Phase 0 + 1 Subagent reicht
- **Daily check** → "Infrastructure Health Audit" section in SKILL.md reicht
- **Basti hat konkrete Symptome** → direkt das spezifische Issue debuggen
- **Post-Update nur** → "Post-Update Checklist" section reicht

## Subagent-Self-Reports — Verifikations-Checklist

Apply BEFORE trusting any "✅ done" from a subagent:

- [ ] File changes: `read_file` or `grep` to see the new state
- [ ] Permissions: `stat -c '%a %n' <file>` 
- [ ] Service state: `systemctl --user status <svc>` with PID + Tasks check
- [ ] Logs: `grep <error> log | awk '{print $1}' | sort -u | tail` — date filter
- [ ] Models: `curl /api/ps | jq` — actual VRAM, ctx, not just "loaded"
- [ ] Skills: `hermes skills list | grep <name>` — Status column
- [ ] Crons: `hermes cron list | grep -A 6 <name>` — last_status field
- [ ] Tools: `hermes tools list | grep <name>` — enabled/disabled
- [ ] Config: `hermes config get <key>` or `grep` in config.yaml

If any verification fails → re-execute the fix in parent.
