# Drift-Aware Security Audit Report Pattern

**Status:** Validated 2026-07-17 (System-Audit Basti Zorin OS, ~3h wall-time)
**Extended:** 2026-07-18 (Volume 3 — multi-day drift measurement + CLAUDE.md drift tracking)
**Source reports:** `~/20-Workspace/results/system-audit-2026-07-17.md`, `~/20-Workspace/results/system-scan-2026-07-18.md`

## Purpose

Recurring audits (weekly/monthly baseline-diffs) produce **better reports** when
the report structure enforces comparison against the prior baseline. Without this
pattern, every audit reads as a fresh green-field snapshot — the user can't tell
whether their last fix worked, and a *different* log-bomb vector (new program,
same symptom) can be misdiagnosed as the old one.

Volume 3 (2026-07-18) extended this pattern with two new dimensions:
- **CLAUDE.md/AGENTS.md cross-reference** — project context files drift just as
  much as live system state, and the audit report should validate them too
- **"logrotate SUCCESS ≠ actual rotation"** pitfall — the service can report
  `Deactivated successfully` while the size rule was never evaluated at the
  timer tick, leaving a 3.45 GB file untouched

## The 4 structural elements

### 1. Reality-Check table vs. plan

If the audit was planned in advance (e.g. by a "system audit" planning section
in chat), every **plan assumption** becomes a table row with live evidence:

```markdown
## Reality-Check vs. plan

| Plan assumption | Reality at audit time | Status |
|---|---|---|
| Disk `/` 84%/96G free | 85%/90G | ⚠ +1% overnight |
| Ollama enabled+active | enabled+active, 5 models ~40GB | ✅ |
| `.steampath` removed | gone | ✅ |
| rsyslog filter present, zorin-printers dead | 22 hits (vs. 6.4M pre-filter) | ✅ |
| /var/log/syslog* tiny syslog + 77MB syslog.1.gz | syslog 2.7GB / syslog.1.gz 77MB | ⚠ partial — see §A-new |
```

The "Status" column tells the user at a glance which planned assumptions held
and which didn't — without scrolling through 600 lines.

### 2. Drift table vs. previous audit reports

When previous reports exist at known paths, the new audit references them
explicitly:

```markdown
## Cross-Check vs. previous audits

- 16.07 audit: zorin-printers filter wirkt ✅ (22 hits vs. 6.4M before)
- 17.07 audit: Ollama Debug-Override, logrotate healthy, syslog.1.gz preserved ✅
- NEU seit 16.07: Ollama print_timing-Spam (anderer Vektor, s. §A-new)
- NEU seit 17.07: logrotate SUCCESS but no rotation since 16.07 (s. §A-new)
```

This catches **vector confusion** — the most common recurring-audit failure
mode.

### 3. Read-only disclaimer

```markdown
**Read-only mode:** No service changes, deletions, config edits, or CLAUDE.md edits applied.
```

This sets the contract: every finding's proposed-fix section contains exact
commands, but the agent did NOT run them. The user sees proposals with risk
stars (⭐/⭐⭐/⭐⭐⭐ from the system-security-audit pattern) and approves
individually.

### 4. CLAUDE.md / AGENTS.md / GEMINI.md drift section (NEU 2026-07-18)

Project context files (`~/CLAUDE.md`, `~/AGENTS.md`, `~/GEMINI.md`) are part of
the recurring-audit baseline. They drift when the system changes (Ollama state,
disk figures, stale file references) but the docs don't. Three recurring
findings from Volume 3 (2026-07-18):

| Fact in CLAUDE.md | Live reality | Status |
|---|---|---|
| "Ollama disabled+inactive" (resolved-history line) | enabled+active with OLLAMA_DEBUG=0 override | 🔴 Stale — wrong since 16.07 |
| Disk 81%/110G free | 85%/89G free | 🔴 Stale — off by -21G |
| `.steampath` dangling symlink | file removed since 17.07 | 🔴 Stale — gone 2 days |
| CPU temp monitor absent | Package temp 86°C idle, crit 100°C | 🟡 Missing watch-item |

**Verification commands for the Drift section:**

```bash
# CLAUDE.md vs. reality: 4 key cross-checks
grep -nE 'Ollama|Disk|steampath|CPU temp' ~/CLAUDE.md | head -10
systemctl is-active ollama          # is Ollama really disabled?
df -h / | awk 'NR==2{print $5, $3}'  # real disk usage
test -f ~/.steampath && echo "present" || echo "gone"
sensors | grep "Package id 0"        # real CPU temp
```

**When to trigger:** Every recurring audit. The Drift section goes BEFORE the
findings, because stale CLAUDE.md references mislead both user and agent. Fixing
doc-drift is a quick win (P3) with high leverage (next session starts clean).

## When to use this pattern

| Trigger | Use pattern? |
|---|---|
| First audit, no prior baseline | ❌ Use plain Section 0 (Multi-Scout) |
| Recurring audit (weekly/monthly) AND a previous report exists | ✅ Use this (all 4 elements) |
| User asks "verify my last fix held" | ✅ Use this — the Reality-Check table IS the answer |
| Sudden incident (service down, port open) | ❌ Use Layer 4 audit pattern instead |
| User says "schnell mal checken" | ⚠ Mini-version (only Reality-Check + CLAUDE.md Drift) |

## When NOT to add complexity

- **Don't add the Drift table if there's nothing to drift against** — it just
  becomes ceremony. First-audit → plain report.
- **Don't write a 600-line audit for a single issue** — the pattern is for
  broad sweeps. Single-issue audits stay short.
- **Don't auto-apply any fix** even if the user says "go ahead" — the read-only
  disclaimer is structural, not stylistic.

## Companion pitfall: logrotate "SUCCESS ≠ actual rotation"

This pitfall lives in the `syslog-source-first-audit` skill (not patchable by
agent — authored manually). Summarised here for cross-reference:

**Symptom:** `systemctl status logrotate.service` shows `Deactivated successfully`,
but `ls -la /var/log/syslog*` shows no new compressed file — the active syslog
keeps the same size and mtime.

**Root cause:** The logrotate timer evaluates `size 500M` only at the daily tick.
If the tick fires while the file is actively growing (pre-2026-07-18: Ollama
writing), the size check may evaluate before growth pushes it past the threshold.
On the *next* timer tick (24h later), the file is already 6+ GB and CAN still be
rotated, but logrotate doesn't check back — it runs once per tick.

**Verification:**
```bash
# Check actual rotation, not just service status:
stat -c '%y %n' /var/log/syslog*       # syslog.1.gz mtime = last actual rotation
journalctl -u logrotate --since "7 days ago" | head -10  # service status (can lie)
```

**Fix:** `sudo logrotate -f /etc/logrotate.d/rsyslog` forces immediate rotation
regardless of conditions.

## Cross-references

- `~/20-Workspace/results/system-audit-2026-07-17.md` — full 664-line report (Volume 2)
- `~/20-Workspace/results/system-scan-2026-07-18.md` — 31.7 KB report (Volume 3)
- `~/20-Workspace/results/security-audit-2026-07-16.md` — previous audit baseline (Volume 1)
- `~/.hermes/docus/audits/2026-07-17-full-audit-report.md` — overnight recovery
- `references/network-service-audit.md` — Layer 4 audit pattern (for incidents)
- `references/fix-block-delivery-pattern.md` — interactive sequential-fix pattern
