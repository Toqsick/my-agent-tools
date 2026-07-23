# Spec-Building Pipeline — Coordinated Multi-File Document Dispatch (🅱️ Variant)

> **Validated:** 2026-07-14 (Sim09+Sim10 15-Lessons → 5 Specs, 3 Bees, 88 KB total)
> **Origin:** Yuno B-Standard-Pattern, Hermes-V7 Skill-Mandatory-Set Build
> **Pattern Family:** 🅱️ Standard (multi-agent-cluster-patterns), queen-bee-schwarm-dispatch

---

## Trigger

Use this technique when:

- You need **N coordinated document files** (specs, reports, briefings) that must share cross-references
- The files are **interdependent** — each references the others' content
- A single agent would produce them sequentially (slow), but they are **logically parallelisable**
- The deliverable is a **document set** with a master index/summary file

---

## The Pipeline (5 Phases)

```
Phase 1: Briefing File         ← Queen writes single source-of-truth
Phase 2: Dispatch N Bees       ← N bees parallel (each gets full briefing)
Phase 3: Queen Validates       ← Read each file, check cross-refs
Phase 4: Cross-Ref Validation  ← Verify specs reference each other correctly
Phase 5: Master-Summary        ← Queen aggregates into single index doc
```

---

## Phase 1: The Unified Briefing File

Write a **single briefing file** that contains ALL constraints and references for ALL bees. Every bee reads the COMPLETE brief — not just their slice.

### Must-Have Sections

```markdown
# [Project-Name] Spec Briefing

## Context
- Was ist das Ziel? (1-2 Sätze)
- Welche simulierten Erkenntnisse liegen zugrunde?
- Welcher Cron-Mode-Blocklist-Ausnahmezustand (write_file only, kein heredoc)?

## Constraints
- Sprache: Deutsch (Spec-Inhalt), Englisch (Code/YAML)
- Größen-Limit pro File: < 30 KB
- Kein MiroFish-Start, keine API-Calls — nur Markdown schreiben
- Tool: write_file only (kein terminal für File-Writes)

## Template (per Spec)
Jede Spec hat diese Sections:
1. **Why** — Befund-Erklärung
2. **YAML-Beispiele** — Positiv + Negativ
3. **Implementation-Skelett** — Python-Pseudo-Code 10-40 Zeilen
4. **Validation-Logic** — Wie testen?
5. **Cross-References** — Zu welchen anderen Specs?

## Complete Lesson List
### Lesson 1: ...
### Lesson 2: ...
### Lesson 3: ...
### Lesson 4: ...
### Lesson 5: ...

## File-Assignment
- Biene A: Spec 1 (lesson-01-...) + Spec 2 (lesson-02-...)
- Biene B: Spec 3 (lesson-03-...) + Spec 4 (lesson-04-...)
- Biene C: Spec 5 (lesson-05-...)
```

### Why a unified brief instead of per-bee slices?
- **Cross-references stay consistent** — each bee knows what the OTHERS are writing
- **No "but I didn't know about X"** — all constraints visible upfront
- **Queen can re-read the same brief later** for validation
- **Validation check-list comes from the same source**

---

## Phase 2: Dispatch Bees

Dispatch all bees **in one wave** (single `delegate_task` call or 3 parallel calls).  
Each bee gets the **same briefing file path** + their specific assignment.

### Briefing per bee (template)

> **Du bist Spec-Biene [A/B/C].**  
> **Kontext:** {cron-mode-blocklist, language, size-limit}  
> **Lies:** `/tmp/briefing-file.md`  
> **Erstelle:** `lesson-XX-[name].md` in `~/docs/system/skill-system-specs/`  
> **Deine Specs (aus dem Briefing):**  
>   - Spec X: Sections 1-8  
>   - Spec Y: Sections 1-5  
> **Validation:** `ls -la` + `wc -l` auf deine Outputs  
> **Rückgabe (deutsch, 1 Absatz):** Status, Datei-Liste mit Größe, Verbesserungsvorschläge, Cross-Reference-Hinweise für andere Bienen.

### Tool restrictions (mandatory in briefing)

```yaml
allowed: [read_file, write_file, terminal (ls/wc only)]
blocked: [web_search, web_extract, delegate_task, clarify, sudo, git]
```

---

## Phase 3: Queen Validates Bee Outputs

When bees return, **read each file** (head -30 or full read) to verify:

| Check | Method | Acceptance |
|---|---|---|
| File exists | `ls -la` | All N files present |
| Size within limit | `wc -c` | < 30 KB each |
| Frontmatter/YAML intact | `head -10` | Valid YAML + Spec-ID |
| Required sections present | grep Section header | All N sections |
| YAML examples present | grep YAML | >= 2 examples (pos+neg) |

---

## Phase 4: Cross-Reference Validation (CRITICAL)

This is the **key innovation** over standard 🅱️ dispatch.  
Because bees wrote independent files that reference each other, the queen MUST verify that cross-references are consistent across ALL files.

### Step 1: Extract Cross-References from Each Spec

```bash
grep -n "Cross-Reference\|lesson-\|Spec[- ]" lesson-01-*.md
grep -n "Cross-Reference\|lesson-\|Spec[- ]" lesson-02-*.md
# ... for all N files
```

### Step 2: Verify Link Validity

```bash
grep -ohP 'lesson-\d+-[\w-]+' *.md | sort -u
ls lesson-*.md | sed 's/.md//'
# Missing refs = files that don't exist at referenced paths
```

### Step 3: Check Cross-Reference Hints from Bees

Each bee's return message may contain **cross-reference hints for other bees**. Collect these:

```markdown
### Biene A's Hints for Biene B:
- Lesson 3 threshold=0.80 must be consistent with Lesson 1
- Disclosure-Rate as reset-hint for WIP-Limit

### Biene A's Hints for Biene C:
- Lesson 5 should document trigger-condition for automated-cluster-saturation reviewer
- Lesson 5 should specify `detect_disclosure_drift(skill)` function
```

### Step 4: Validate Critical Cross-Ref Pairs

For spec sets, certain cross-ref pairs are CRITICAL:

| Pair | What to check |
|---|---|
| Spec 1 -> Spec 3 | Threshold value (e.g., 0.80) consistent? |
| Spec 1 -> Spec 5 | Trigger condition for automated reviewer mentioned? |
| Spec 2 -> Spec 5 | Disclosure-drift-detection function specified? |
| Spec 3 -> Spec 5 | Same cluster skeleton definition used? |
| Spec 4 -> Spec 2 | Disclosure-Rate as WIP-Reset consistent? |

---

## Phase 5: Master-Summary Aggregation

Write a **single master-summary file** that:

1. **Lists all N spec files** with sizes and status
2. **Shows the interconnection map** — which spec references which
3. **Documents the bee dispatch** — who built what
4. **Provides implementation roadmap** — priority order
5. **Includes threshold calibration caveats**

### Master-Summary Template

```markdown
# [Project] Master Summary — Mandatory Set

> **Generated:** {date}
> **Pattern:** Yuno B-Standard 🅱️ (N bees parallel, Queen Quick-Ack)
> **Source:** {research / simulation data}

## Overview

| # | Spec | Size | Source | Tier |
|---|---|---|---|---|
| 1 | [Name](./file.md) | X KB | SimXX | 🔴 Safety |

## Interconnection Map

```
[1 Spec] <------- [3 Spec] <-- cluster-skeleton
    |                    |
    v                    +-- threshold: 0.80
[2 Spec] --------> [5 Spec] <-- saturation check
```

## Bee Dispatch (B-Standard Quick-Ack)

- **Biene A** (specs): File1 (X KB) + File2 (Y KB) -- ✅
- **Biene B** (specs): File3 (Z KB) + File4 (W KB) -- ✅
- **Biene C** (spec): File5 (V KB) -- ✅

## Implementation Roadmap

### Priority 1 (Week 1-2)
...
### Priority 2 (Week 3-6)
...

## Known Limitations
- Threshold X was calibrated on N-posts corpus -- re-calibrate for smaller sets
- Cross-spec consistency was validated once -- re-verify after any single-spec edit
```

---

## Lessons from 2026-07-14 Build (Sim09+Sim10 -> 5 Specs, 88 KB)

### What Worked
- **Unified briefing file** — all 3 bees had the same context, cross-references stayed consistent
- **Single-wave dispatch** — no dependency between specs (all parallelisable)
- **Bee-return hints** — Biene A delivered 2 cross-ref hints for Biene B+C that were NOT in the brief
- **Master-summary in < 1 min** — queen aggregated 3 bee returns into a single coherent document

### What to Watch
- **Spec size creep** — specs were 30-60% over the 5-8 KB target (12 KB actual). Mitigation: extract validation-test-matrix into `references/` subfiles.
- **Cross-ref validation is manual** — no automated tool checks. Queen must grep + verify.
- **Threshold drift** — if single spec is updated later, the master-summary and other specs' cross-refs MUST be re-verified.

### Anti-Patterns
- ❌ Giving each bee ONLY their slice of the brief (they can't cross-reference correctly)
- ❌ Trusting bee self-reports for cross-ref consistency (queen MUST grep the actual files)
- ❌ Writing master-summary without re-reading all bee outputs (hallucination risk)
- ❌ Editing a single spec later without re-verifying all cross-refs in the set