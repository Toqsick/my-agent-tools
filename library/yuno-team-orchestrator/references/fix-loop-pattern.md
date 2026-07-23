# Multi-Persona Fix-Loop Pattern

Wann eine einzelne Persona-Runde nicht reicht: **Iterative Loops** zwischen Engineer/Writer/Researcher und Verifier.

## Wann einen Fix-Loop fahren?

**Trigger:**
- Verifier sagt FAIL mit ≥ 3 HIGH/MED Bugs
- Erste Subagent-Runde hat "klappt" berichtet aber Tests sind dünn (nur Happy-Path)
- Deliverable geht in Production oder wird von anderen Personas weiterverarbeitet

**Nicht sinnvoll für:**
- Reine Info-Tasks (Researcher-Anfrage → fertig)
- Tasks mit ≤ 2 Trivial-Bugs (Inline-Fix im Parent, kein Subagent)
- Wenn die Ursache unklar ist (erst Researcher ran, dann Engineer)

## Das Pattern

```
Phase 1: BUILD
  └─ Engineer-Subagent (oder Writer/Researcher/Analyst)
  └─ Deliverable: code + tests + sample data

Phase 2: AUDIT
  └─ Verifier-Subagent (Gate-Persona, multi-domain)
  └─ Deliverable: VERDICT + Strengths + Issues (file:line, repro, fix hint) + Risks

Phase 3: FIX
  └─ Producer-Subagent (Engineer bei Code, Writer bei Doc, etc.)
  └─ Briefing = komplette Verifier-Bug-Liste mit file:line + Repro
  └─ Deliverable: gefixter Code + neue Tests für jeden Bug + Verification-Report

Phase 4: RE-AUDIT
  └─ Verifier-Subagent (gleiche Persona)
  └─ Briefing = Liste der "claimed fixed" Bugs + Phase-2-Findings
  └─ Deliverable: PASS / NEEDS-FIX (mit neuen Regressions)

Phase 5: LOOP-CHECK
  └─ PASS → Final-Synthese, Doku
  └─ NEEDS-FIX → zurück zu Phase 3 mit kombinierter Bug-Liste
  └─ Max 3 Iterationen, sonst Scope-Ballon → parent-direct-Übernahme
```

## Briefing-Template: Engineer-Fix-Run

```text
═══════════════════════════════════════════════════════════════════
FIX-LOOP RUN — Verifier found N HIGH/MED bugs in <FILE>.
Fix them in priority order, then re-run the test suite.

WORKING DIR: <abs path>
EXISTING FILES: <file list with line counts>

BUGS TO FIX (in priority order, with file:line and exact repro):

═══ HIGH SEVERITY ═══
Bug #N (<file>:<line>) — <one-line description>
   Repro: <exact shell command>
   Root cause: <mechanism>
   Fix: <concrete suggestion>

═══ MED SEVERITY ═══
...

═══ LOW SEVERITY (fix opportunistically if cheap) ═══
...

═══ TEST REQUIREMENTS ═══
Add ONE pytest test per HIGH/MED bug (so N new tests minimum):
- test_<bug_name> — <input> → <expected exit + behavior>

═══ VERIFICATION BEFORE DECLARING DONE ═══
1. All N existing tests still pass
2. All M new tests pass
3. Manual repro of each Verifier-Bug → expected exit, NO traceback
4. Stdlib-only / no extra deps confirmed
5. Math/spot-checks unchanged

═══ OUTPUT FORMAT ═══
- File list with line counts (before/after)
- Test results: PASS/FAIL count
- Bug-by-bug: which fix you applied (file:line) and confirmation
- Any bugs you deliberately did NOT fix + why
```

## Briefing-Template: Verifier-Re-Audit

```text
═══════════════════════════════════════════════════════════════════
RE-AUDIT — <Producer> applied fixes for the N HIGH/MED bugs you found
in the previous round. Verify each fix actually works AND look for
NEW regressions the fixes may have introduced.

CONTEXT FROM PREVIOUS ROUND (your own findings, now claimed fixed):
1. HIGH Bug #N: <description> → fixed by <hint>
2. ...

YOUR JOB (4 phases):

═══ PHASE 1: Confirm fixes ═══
Re-run each Verifier repro from last round. For each, confirm:
- Exit code matches spec
- NO Python traceback leaked
- Output is reasonable (not garbage)

═══ PHASE 2: Adversarial regression hunt ═══
The fixes may have introduced NEW bugs. Try:
- <list of regression-inputs that exercise edge cases of the fix>

═══ PHASE 3: Run the test suite yourself ═══
`cd <path> && python3 -m pytest tests/ -v`
Confirm N/N pass. If anything fails, that's a regression.

═══ PHASE 4: Read every file end-to-end ═══
Look for: TODOs/FIXMEs/XXX left in shipped code, anti-patterns
(giant patches, invented APIs), any logical gaps.

═══ OUTPUT FORMAT ═══
- VERDICT: PASS | FAIL | NEEDS-FIX
- Per-bug confirmation: Bug #N — confirmed fixed / NOT fixed / PARTIAL
- New issues (numbered, with file:line and fix suggestion)
- Risk callouts
- Re-test plan

BE ADVERSARIAL. If you can't break it, say so explicitly with the inputs you tried.
```

## Lessons aus dem CSV-Summary-Loop (2026-07-07) — Komplett

### Setup

Engineer baute csv_summary.py (293 LoC, 9 Tests grün) mit Stdlib-only, 12x6 Sample-Daten.

### Loop-Verlauf

| Loop | Persona | Dauer | Ergebnis |
|------|---------|-------|----------|
| 1 | Engineer (Build, cold) | 223s | 293 LoC, 9/9 grün |
| 2 | Verifier (Audit, cold) | 196s | **FAIL** — 8 Bugs (6 HIGH/MED + 2 LOW) |
| 3 | Engineer (Fix, cold) | 153s | +89 LoC (+6 Tests), 15/15 grün |
| 4 | Verifier (Re-Audit) | 243s | **PASS** — 14 Regression-Inputs, 2 NEUE Bugs (#9 BOM, #10 dup headers) |
| 5 | Engineer (Fix #2) | 97s | +28 LoC (+2 Tests), 17/17 grün |
| 6 | Verifier (Final Re-Audit) | ~200s | PASS (oder neue Findings) |

### Key Insights

1. **Warm-Subagents sind 2.3× schneller** — Engineer Run 5 (97s) vs Run 1 (223s). Grund: der Code ist bereits im Subagent-Kontext, kein Fresh-Read + keine Initial-Environment-Friction.
2. **Verifier kann 8 echte Bugs in 196s** in einem 293-LoC-Tool finden — gegen self-tests grüne Coverage. Loop ist nicht optional.
3. **Engineer kann 6 HIGH/MED + 3 LOW in 153s** fixen mit vollständiger Bug-Liste im Briefing. Mehr als 6 Bugs = Scope-Ballon-Risiko.
4. **Verifier-Mechanik ≠ Verifier-Repro**: Verifier fand `fmean` overflow-Mechanik korrekt, wählte aber `9999` als Repro-Trigger (zu eng). Parent muss Mechanik prüfen, nicht 1:1 Repro.
5. **Pitfall #5 gilt universell**: Auch Verifier-Self-Reports ("Bug fixed") muss Parent durch eigene Repro bestätigen.
6. **Loop konvergiert schnell**: Verifier fand in Runde 2 noch 8 Bugs, in Runde 4 nur noch 2. Ein dritter Verifier-Loop findet typischerweise 0-1 neue Issues.

### Welche Bugs wurden gefunden?

| # | Severity | Found von | Beschreibung | Fix | Status |
|---|----------|-----------|-------------|-----|--------|
| 1 | HIGH | Verifier (Runde 1) | `fmean`/`stdev` crash auf NaN | `math.isfinite` filter | ✅ |
| 2 | HIGH | Verifier (Runde 1) | Ragged-row detector broken | DictReader → csv.reader + len compare | ✅ |
| 3 | MED | Verifier (Runde 1) | `/etc` input → IsADirectoryError | try/except handler | ✅ |
| 4 | MED | Verifier (Runde 1) | `chmod 000` → PermissionError | same handler | ✅ |
| 5 | MED | Verifier (Runde 1) | Latin-1 → UnicodeDecodeError | `errors="replace"` | ✅ |
| 6 | LOW | Verifier (Runde 1) | `--top 0` silent | argparse `_positive_int` | ✅ |
| 7 | LOW | Verifier (Runde 1) | Path leak in stdout | basename-only display | ✅ |
| 8 | LOW | Verifier (Runde 1) | Long categorical bar truncation | Truncate label | ✅ |
| 9 | MED | Verifier (Runde 2) | BOM leak in column names | `encoding="utf-8-sig"` | ✅ |
| 10 | MED | Verifier (Runde 2) | Duplicate headers silent overwrite | InvalidCSVError | ✅ |
| — | — | — | **10 Bugs total, 0 offen** | — | ✅ |

**Wann aufhören mit dem Loop:**
- Verifier sagt PASS (mit Begründung + aufgelisteten Inputs)
- 3 Iterationen ohne PASS (dann Scope zu groß, parent-direct mit Researcher-Diagnose)
- Neue Regressions überwiegen die Bug-Fixes (→ Refactor statt Patchwork)