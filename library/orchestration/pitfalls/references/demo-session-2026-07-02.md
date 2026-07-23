# Live Demo Session — Cheatsheet First-Run Validation

**Datum:** 2026-07-02
**Hive Lord:** Basti
**Operator:** Yuno (Queen)
**Purpose:** Validate the freshly-built `multi-agent-pitfalls-cheatsheet` skill with a minimal demo spawn, BEFORE running the real GreyHack 3-expert audit next session.

---

## Context

Basti requested Option 2 (cheatsheet skill) + Option 4 (GreyHack 3-expert audit) as a two-phase plan. Phase A = build, Phase B = use. After building the cheatsheet, Basti chose to test it live in the same session with a minimal demo — **against the Workflow Discipline rule** (see SKILL.md §Workflow Discipline). The minimal demo is the documented exception.

---

## Demo Briefing (what was actually sent)

**Goal:** Inventarisiere und beschreibe alle Skills im Verzeichnis `~/.hermes/skills/orchestration/`. Schreibe einen strukturierten Report auf den angegebenen OUTPUT-Pfad.

**Context (verbatim):**
```
SYSTEM: Linux 6.17.0, Ubuntu 24.04, bratan@home. Hermes-Agent mit aktiver Koenigin-Lane. Du bist ein Read-Only-Scout.

AKTUELLER STATE:
- ~/.hermes/skills/orchestration/ enthaelt 6 Skills:
  depps-orchestration, hermes-orchestration, multi-agent-orchestration,
  multi-agent-pitfalls-cheatsheet, research-orchestration, skill-lane-router

AUFGABE:
1. Fuehre `ls -la ~/.hermes/skills/orchestration/` aus und liste alle Unterverzeichnisse auf
2. Lies von jedem Skill die erste 30 Zeilen der SKILL.md (verwende `head -30`) — beschreibe in 1 Satz was der Skill tut
3. Pruefe mit `wc -l` die Dateigroesse jeder SKILL.md und melde sie
4. Erstelle eine Markdown-Tabelle mit Spalten: Skill-Name | Beschreibung (1 Satz) | Zeilen
5. Schreibe den vollstaendigen Report (inkl. Tabelle + Methodik + Discoveries) auf den OUTPUT-Pfad

OUTPUT: ~/docs/system/subagent-demo-2026-07-02.md

WRITE-THE-FULL-REPORT-TO-FILE: Schreibe den vollstaendigen Report als DEINE LETZTE AKTION in die obige Datei. Der summary-Block in deinem Result-Output ist NUR fuer die Status-Anzeige, NICHT ein Ersatz fuer die Datei.

MAX 5 terminal-calls total. Nach 5 Calls -> Report schreiben mit dem was du hast.

OUTPUT-LIMITS: `head -30` ist OK, aber kein `cat` auf ganzen Dateien. Nutze `head`/`wc`/`ls`.

PITFALLS TO AVOID:
- Schreibe NICHT nach ~/.hermes/skills/ (das ist der Skill-Tree, nur SKILL.md erlaubt)
- Behaupte NICHT "done" ohne dass die Datei tatsaechlich existiert
- Nutze KEIN sed, rm, mv, chmod — nur read-commands: ls, cat, head, tail, grep, find, wc
- Wenn Output >100 Zeilen ist: head, wc -l, limit=

VERIFIKATION (was der Parent nach dir checken wird):
- ls -la ~/docs/system/subagent-demo-2026-07-02.md — Datei muss existieren
- wc -l ~/docs/system/subagent-demo-2026-07-02.md — muss >20 Zeilen sein
- grep -c "^|" ~/docs/system/subagent-demo-2026-07-02.md — Tabelle muss Zeilen haben
```

**Toolsets:** `terminal`, `file`

---

## Pre-Spawn Checklist (applied)

| # | Question | Answer |
|---|---|---|
| 1 | Output-Pfad explicit? | YES — `~/docs/system/subagent-demo-2026-07-02.md` |
| 2 | Call-Budget? | YES — `MAX 5 terminal-calls` |
| 3 | Source-Code-Pfade? | YES — `~/.hermes/skills/orchestration/` |
| 4 | Read-only or write? | YES — read-only (ls, cat, head, tail, grep, find, wc) |
| 5 | Verification-Plan? | YES — `ls -la`, `wc -l`, `grep -c "^|"` |

All 5 green. Cleared to spawn.

---

## Pitfalls Mitigated by This Briefing

| Pitfall # | How |
|---|---|
| **#6** Wrong output-path | `OUTPUT: ~/docs/system/...` explicit + "Schreibe NICHT nach ~/.hermes/skills/" warning |
| **#15** Output-Limit | `head -30` allowed, `cat` forbidden |
| **#29** Summary ≠ File | `WRITE-THE-FULL-REPORT-TO-FILE als DEINE LETZTE AKTION` + "summary-Block NUR fuer Status-Anzeige" |
| **#31** Background-Review-Approval timeouts | Read-only commands only, no chmod/rm/mv/systemctl |
| **#5** Phantom-fixes | Verification plan inlined in briefing ("Behaupte NICHT done ohne dass Datei existiert") |

---

## Verification Commands (parent runs after spawn returns)

```bash
# 1. File-existence check
ls -la ~/docs/system/subagent-demo-2026-07-02.md

# 2. Content-size check (must be >20 lines per briefing)
wc -l ~/docs/system/subagent-demo-2026-07-02.md

# 3. Table-presence check (must have | rows)
grep -c "^|" ~/docs/system/subagent-demo-2026-07-02.md

# 4. Section coverage (all 5 task items addressed)
grep -ic "methodik\|discover" ~/docs/system/subagent-demo-2026-07-02.md

# 5. Cross-check vs subagent's result summary (does the file content match the summary?)
cat ~/docs/system/subagent-demo-2026-07-02.md | head -10
```

---

## Reuse Pattern

To validate the cheatsheet in a new session:

1. Pick a small **read-only** directory (≤10 files) under `~/.hermes/` or `~/Dokumente/`.
2. Draft a briefing following the 5-question checklist above.
3. Spawn exactly 1 subagent (not a batch — that's for Option 4 / GreyHack).
4. Run the 5 verification commands above.
5. Compare subagent result-summary vs file-content. Any mismatch = cheatsheet Pitfall #29 fired.
6. Document outcome as `references/demo-session-DATE.md` (new file per validation round).

**Why 1 subagent not 3:** 3-expert spawns trigger the full Pattern + Multiple-Pitfall surface; 1-spawn isolates the briefing → output-pipeline and is a cheaper test for the cheatsheet basics.

---

## Cheatsheet Changes Triggered by This Demo

- **Pitfall #33 added:** YAML/double-quote parsing failures in skill frontmatter and briefings. Triggered when first creating the cheatsheet skill — `triggers:` list-item containing `"phantom fix" / "..."` failed `skill_manage(create)` with `expected <block end>, but found '<scalar>'`.
- **Workflow Discipline section added:** "Build then use in separate session" preference embedded as a behavioral rule.

Both changes are now in SKILL.md and persisted across sessions.