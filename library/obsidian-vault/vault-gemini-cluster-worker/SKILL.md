---
name: vault-gemini-cluster-worker
description: >-
  Use when user asks for dispatching Gemini CLI for Obsidian vault work, assigning a scoped vault cluster to a worker bee, verifying Gemini-created notes, or rolling back out-of-scope vault writes. NOT for general Gemini chat or editing a single note inline. Defines the proven worker call, backup, directory fences, artifact checks, telemetry cleanup, quirks, and rollback procedure.
triggers:
- User asks for "Gemini-Pass" / "Cluster A" / "Subagent mit Gemini-CLI"
- Multi-cluster vault phase planning (Phase 7+, Cross-Links, Design-Rework)
- Need to delegate heavy multi-file edits to a 2nd LLM with restricted scope
when_to_load:
- Setting up a "Gemini worker bee" task prompt
- Verifying Gemini's output against anti-patterns after a run
- Debugging "Gemini modified wrong file" / "Müll-Skripte im Root"
author: Hermes Agent
version: 1.0.0
license: MIT
trigger_keywords: ['vault', 'gemini', 'worker', 'vault-gemini-cluster-worker', 'dispatching']
keywords: ['gemini', 'vault', 'worker', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['gemini-vault-worker', 'obsidian-vault-cluster-operations', 'obsidian']
---


# Vault-Gemini Cluster Worker — Pattern (Phase 7-9 lessons)

## What this is

The **Worker-Bee-Architecture**: Yuno (Queen-Bee, MiniMax-M3) plans a vault
phase, divides work into **clusters** (A = Gemini-CLI subagent, B = inline),
and dispatches Gemini with a tightly scoped prompt + `--yolo` flag for
additive file operations. The user (Basti) is on Google AI Pro with
`gemini-3.1-pro-preview` always.

## Proven call pattern (Basti, 2026-07-05, Phase 7+8+9)

```bash
cd "/home/bratan/Dokumente/Obsidian Vault"
PROMPT="$(cat '05 Ressourcen/Vault-Phase-N-Plan.md')

---

ZUSÄTZLICHER AUFTRAG FÜR DICH (GEMINI, mit --yolo Schreibtools aktiv):
<scope, baseline-befunde, anti-patterns, deliverables, final-report-format>"
timeout 900 gemini --yolo \
  --include-directories "/home/bratan/Dokumente/Obsidian Vault" \
  -m gemini-3.1-pro-preview \
  -p "$PROMPT" 2>&1 | tee /tmp/gemini-phaseN.log
```

- **timeout:** 900s (foreground max 600s → use `background=true` + `notify_on_complete=true`)
- **`--include-directories`:** scopes Gemini's allowed paths (workspace lock still rejects `/tmp/*` writes — Gemini falls back to `~/.gemini/tmp/<project>/`)
- **`-m gemini-3.1-pro-preview`:** always, Basti-preference (Tradeoff: >90s response possible)
- **`2>&1 | tee /tmp/gemini-phaseN.log`:** ALWAYS tee, because Gemini's final report is the only structured output the user sees

## Anti-Patterns (Gemini MUST NOT do these)

These are the **9 hard rules** proven by Phase 8 lessons. Always include them
verbatim in the Gemini prompt:

1. ❌ Override existing CSS-snippets completely
2. ❌ Change Yuno color palette (`yuno-variables.css`)
3. ❌ Override Sanctum theme base
4. ❌ Touch vault-notes outside the agreed scope (MOCs / Snippet-Liste / Plugins-Setup / Skill-Ableitung)
5. ❌ Replace MOCs completely (only additively patch)
6. ❌ Drop Müll-Skripte (Python/Shell) in vault-root (Phase-8-Lesson!)
7. ❌ Overwrite `07 Archiv/` content (only additively OK)
8. ❌ Fabricate facts (Pattern 3 Anti-Halluzination)
9. ❌ Delete/move `.obsidian.backup-*` folders — only report recommendation

## Verification checklist (Pattern 7-Critical — always run after Gemini)

After every Gemini run, the Queen-Bee or a verifying subagent MUST run:

```bash
cd "/home/bratan/Dokumente/Obsidian Vault"
# 1. Notes-Anzahl delta
find . -name "*.md" -not -path "./.obsidian.backup-*" -not -path "./.trash/*" | wc -l
# 2. Müll-Skripte im Root (Phase-8-Lesson)
find . -maxdepth 1 \( -name "*.py" -o -name "*.sh" \) -type f
# 3. Verbotene Folder mtimes (last 30 min)
find "01 Kontext" "02 Inbox" "07 Archiv" "08 Anhaenge" -name "*.md" -newermt "<start-of-run>"
# 4. CSS-Snippet mtimes (should be untouched)
ls -la .obsidian/snippets/*.css
# 5. New notes count + grep scope-deliverables
find . -name "*.md" -newermt "<start-of-run>"
```

If **any** of #2, #3, #4 is non-empty → ROLLBACK candidate, document in final-report.

## Scope clarification — Cluster A vs Cluster B

Always define clusters explicitly in the plan:

| Cluster | Worker | Scope | Anti-patterns |
|---|---|---|---|
| A | Gemini-CLI subagent | MOCs, Snippet-Liste, Plugins-Setup, Skill-Ableitung, CSS-Doku | 9 anti-patterns above |
| B | Yuno inline (MiniMax-M3) | Working Agreement, Mnemosyne commit, Telemetrie-deakt, Hermes-Skills | Different: file-touch scope is Working Agreement + Hermes-skill files |

Gemini has a tendency to "helpfully" do Cluster B work too (observed in Phase 9
— Gemini added "Gemini-CLI Worker-Pattern" section to Working Agreement even
though that was Cluster B). **Prevention:** explicitly tell Gemini which
files it must NOT touch.

## Gemini response style

Gemini's `--yolo` run gives:
- A short final-report block at the end (usually the only structured output)
- Free-form reasoning before that (often truncated)
- Workspace-lock errors when it tries to write outside `--include-directories`

**Always trust the final-report with empirical verification.** Gemini's
claims ("I have updated 4 files") may be half-true if `replace` failed
silently. Hence Pattern 7-Critical.

## Backup-before-run (Pattern 7-Critical)

```bash
BACKUP_DIR=~/.cache/vault-backups/phaseN-$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
rsync -a "/home/bratan/Dokumente/Obsidian Vault/" "$BACKUP_DIR/vault/"
```

Always do this BEFORE the Gemini prompt is sent. Don't ask Gemini to do it
(Gemini under --yolo may not properly handle rsync).

## Telemetrie (separate cleanup)

`DISABLE_TELEMETRY=1` in `~/.gemini/.env` removes "Error flushing log events"
spurious output. Set this once, persists across runs.

## Known Gemini quirks (Phase 9 findings)

- **Workspace lock:** writing to `/tmp/foo.py` fails → falls back to `~/.gemini/tmp/<project>/` (acceptable)
- **Off-by-one notes count:** always count before & after; Gemini may add 1-2 notes extra (e.g. duplicate skill-derivation when one already exists)
- **Dataview-Plugin assumption:** Gemini assumes Dataview is installed by default — reality: installiert + aktiviert via `community-plugins.json` + `.obsidian/plugins/dataview/`, aber vor jedem Lauf `ls .obsidian/plugins/` re-verifizieren (Drift-Schutz). JS-Queries müssen in Obsidian-Settings explizit ON sein.
- **Cleanup pass:** Gemini reads `.obsidian.backup-*` and lists them, but does NOT delete them — exactly right (Pattern 9)
- **Orphan-scan:** Gemini writes a Python scanner to its own tmp dir, runs it, reports findings — good pattern, no vault pollution

## Rollback procedure (if verification fails)

```bash
# From backup (pre-run):
rsync -a --delete ~/.cache/vault-backups/phaseN-*/vault/ "/home/bratan/Dokumente/Obsidian Vault/"
# From Gemini tmp (if Gemini wrote outside allowed dirs):
ls -la /home/bratan/.gemini/tmp/<project>/  # usually safe to leave
```

## Related Skills (registered in ~/.hermes/skills/)

- `obsidian-vault-cluster-operations` — the umbrella vault-cluster skill (Gemini is a Worker-Bee tool for it)
- `subagent-driven-development` — Pattern for executing plans via delegate_task
- `bash-script-audit` — for cleanup-pass scripts Gemini writes

## Verbindet zu

- `Working Agreement - Yuno Basti` § "Gemini-CLI Worker-Pattern" (Cluster B update)
- `05 Ressourcen/Skill-Ableitung - Vault-Phase-7-8.md` — Gemini-CLI patterns from Phase 7+8
- `05 Ressourcen/Skill-Ableitung - Vault-Phase-7-8-9.md` — extended Phase 9 patterns (optional, see if Queen-Bee accepts)
- `Vault-Phase-7-Plan`, `Vault-Phase-8-Plan`, `Vault-Phase-9-Plan` — the planning phase artifacts