---
name: skill-library-maintenance
description: |
  Use when you need to use the skill-library-maintenance workflow and its documented procedures.
  NOT for unrelated tasks outside the skill-library-maintenance workflow.
  Provides focused guidance for skill-library-maintenance.
version: 2.2.0
author: Yuno (Basti)
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - skills
    - maintenance
    - library
    - optimization
    - slim-down
    - references
    - context-optimization
    category: software-development
    related_skills:
    - hermes-agent-skill-authoring
    - skill-install-workflow
    - multi-agent-pitfalls-cheatsheet
    - multi-agent-orchestration
    - skill-navigator
    changelog:
    - 2.2.0 (2026-07-16): 'Step 4 upgrade — Python broken-ref scanner replaces bare grep pipeline. New 3-category framework (BUNDLE_MISSING / FILE_MISSING / TEMPLATE_PLACEHOLDER) with P0-P2 priority scheme. Bundle-Skill type-error pitfall (#37). Verified by 491-skill audit — 265 broken refs categorised. Refs: broken-ref-categorization.md.'
    - 2.1.0 (2026-07-07): 'New section "Health Audit (Comprehensive)" — 10-dimension
        scan protocol covering frontmatter, permissions, broken links, secrets, duplicates,
        manifest integrity, and storage. Added proactive-fix stance for non-security
        findings. Added Pitfall #34 (shell scripts without +x), #35 (manifest orphan
        drift), #36 (SHA-manifest misalignment). Verified by full 248-skill audit
        — 24 scripts + 17 broken links + 7 manifest orphans fixed. Report: `~/docs/system/skills-audit-2026-07-07.md`.
        Reference: `references/health-audit-2026-07-07.md`.'
    - 1.9.0 (2026-07-04): 'New section "Hub-Imported Resolution" — covers systematic
        hub-imported/ directory cleanup: frontmatter-based dedup (not dir-name), active-skill
        SHA256 snapshot for integrity, diff -r verification for moved skills, category-target
        classification for unique skills. Verified by session — 21 skills resolved
        (13 duplicates deleted, 8 moved to creative/ + media/). Added Pitfall #31
        — hash before, not after.'
    - 1.8.0 (2026-07-04): New section "Archive (.archive/) Management" — covers 0-risk
        duplicate snapshot removal, reanimation candidate flow, diff-check, and model
        selection (Fable vs OPUS) for skill audit. Verified by session — 2 duplicate
        batches (302 SKILL.md, 19MB) removed with 0 data loss; 11 reanimation candidates
        found via fuzzy-match; OPUS 4.8 confirmed Fable's "all dead" claim was false.
    - 1.6.0 (2026-07-02): New section "Cross-Domain Skill Linking" — documents when
        and how to add domain↔method skill cross-references (gaming→orchestration
        pattern). Added `skill-navigator` to related_skills. Verified by 4 GreyHack
        skills + 3 orchestration skills patched in one session.
    - 1.5.0 (2026-07-03): Round-2 final patches — Pitfall
    - 1.3.0 (2026-07-03): Pitfall
    - 1.2.0 (2026-07-03): Pitfall
    - 1.1.0 (2026-07-03): Round-2 patterns — re-scan between rounds (Pitfall
    - 1.0.0 (2026-07-02): Initial release — 16 pitfalls from Round-1 mission, 9 skills
        slimmed 33-105KB → 6-14KB across 2 waves, 26 broken refs caught + fixed.
lane: worker-heavy
reasoning_effort: low
trigger_keywords: ['skill', 'library', 'maintenance', 'workflow', 'need']
keywords: ['skill', 'library', 'maintenance', 'workflow', 'need']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['voice-clone', 'github-workflow', 'multi-agent-pitfalls-cheatsheet']
---


# Skill Library Maintenance

Systematic care of the `~/.hermes/skills/` library: detect oversized monoliths, extract bulk into `references/`, deduplicate, and keep context-load costs low.

## When To Use

- User asks to "scan", "slim down", "clean up", or "verschlanken" the skill library
- Skill sizes have grown large after active development phases
- `skill_view` loads are slow or consume too much context
- Periodic health check (e.g. monthly)
- User asks "schau mal ob alle skills funktionsbereit sind" / "sind alle skills ready?" / health audit
- Before/after skill library migration or curator run
- Before building export bundles (ensures all source skills are intact)

## Don't Use For

- Creating a single new skill (use `hermes-agent-skill-authoring` for in-repo, `skill_manage(action='create')` for user-local)
- Installing external skills (use `skill-install-workflow`)
- Editing skill content (just patch the specific skill)

---

## Health Audit (Comprehensive)

Multi-dimensional health check of ALL skills — not just size. Captures permission, frontmatter, broken-link, secret, duplicate, manifest-integrity, and storage metrics in one pass.

**Proactive Fix Stance:** Non-security findings (broken links, missing execute bits, manifest orphans) are fixed immediately. Security findings (API keys, credentials) require read-only → approval.

→ See `references/health-audit.md` for 10-dimension scan protocol, output template, and fix strategies.
→ See `references/fix-strategies.md` for broken links, shell script permissions, manifest orphans, SHA regeneration, and fix classification table.

### 11 Dimensions (+ 1 optional)

1. **Frontmatter** — YAML parse check (every SKILL.md)
2. **Permissions** — shell scripts without +x
3. **Broken links** — markdown `[text](path)` that don't resolve AND bare-path inline `references/X.md` / `scripts/Y.sh` mentions pointing to nonexistent files
4. **Secrets** — hardcoded tokens in skill files
5. **Duplicates** — skills with same `name:` field
6. **Manifest** — orphan entries in `.bundled_manifest`
7. **Storage** — total bytes, active skill count
8. **Python syntax** — `python3 -m py_compile` on all `*.py` files
9. **Monoliths** — SKILL.md >500 lines (line count, not just byte size)
10. **Token budget** — SKILL.md >25KB (practical context-window cost)
11. **Extraction candidates** — SKILL.md >200 lines with no `references/` directory

**Report location:** `~/docs/system/skills-audit-YYYY-MM-DD.md`

---

## Diagnostic Scan

### Step 1: Size Inventory

```bash
find ~/.hermes/skills -name "SKILL.md" \
  -not -path "*/.archive/*" -not -path "*/duplicates*" \
  -exec wc -c {} \; | sort -rn | head -25
```

**Thresholds:**
- >40KB = urgent (monolith, heavy context cost)
- 25–40KB = candidate (moderate extraction needed)
- >500 lines = monolith (stronger token proxy than byte size alone)
- >200 lines + no `references/` dir = extraction candidate
- <25KB = OK (no action)

### Step 3: Python Syntax Check

```bash
find ~/.hermes/skills -name '*.py' -not -path '*/.archive/*' \
  -exec python3 -m py_compile {} \; 2>&1 | grep -v '^\s*$'
# Expected output: nothing (clean). Any SyntaxError is a P0 bug.
```

### Step 4: Broken Reference Scan (Categorised)

→ See `references/broken-ref-categorization.md` for the 3-category framework (BUNDLE_MISSING / FILE_MISSING / TEMPLATE_PLACEHOLDER) and P0/P1/P2 priority scheme.
→ See `scripts/broken-ref-scanner.py` for the re-runnable Python scanner with JSON output and Top-N listing.

```bash
# Quick categorised scan (stdout summary)
python3 ~/.hermes/skills/software-development/skill-library-maintenance/scripts/broken-ref-scanner.py

# Full JSON output for programmatic processing
python3 scripts/broken-ref-scanner.py --json /tmp/broken-refs.json

# Custom Top-N (default 20)
python3 scripts/broken-ref-scanner.py --top 30
```

**Key outputs:**
- Bundle-Skill count: skills with no `references/` AND no `scripts/` dir
- Bundle-Skill type errors: skills that claim bundle refs without having bundle dirs
- Clean Bundle-Skills: single-file skills that correctly omit bundle refs (no action needed)
- FILE_MISSING count: skills with bundle dirs but specific files absent

| Category | Criteria | Action |
|----------|----------|--------|
| **Monolith** | >25KB SKILL.md + 0 reference files | High priority — create `references/` |
| **Partial** | >25KB SKILL.md + has `references/` | Medium — move more content out |
| **OK** | <25KB | No action |

→ See `references/slim-down-protocol.md` for full extraction protocol, delegation template, and post-slim-down verification.

---

## Slim-Down Summary

**Keep in SKILL.md (target: 8–15KB):**
- YAML frontmatter (EXACT as-is — never modify)
- Intro / "When To Use" section
- Short section outlines (name + 1–2 sentences)
- Critical pitfalls/warnings (bullet form)
- Code snippets ≤10 lines
- One-line pointers: `→ See references/<file>.md for details`

**Extract into `references/`:**
- Detailed step-by-step instructions
- All code blocks >10 lines
- Bug logs, changelog entries, fix histories
- Deep-dive explanations, API details, production evidence

## Batch Delegation Pattern

For slimming 5+ skills, delegate to subagents in parallel waves of up to 5:

- Each subagent gets ONE skill + the full extraction protocol
- Subagent reads SKILL.md → creates `references/` files → rewrites lean SKILL.md
- Include explicit target size in the goal
- **Verify after each wave**: frontmatter intact, SKILL.md ≤ target, reference files exist and are non-empty

**Critical:** Subagents must NOT modify the YAML frontmatter. Include this as an explicit instruction.

---

## Archive (.archive/) Management

Goal: distinguish **redundant snapshots** (safe to delete) from **reanimation candidates** (skills that exist only in archive, not in active use).

→ See `references/archive-management.md` for diagnostic scan, 0-risk duplicate removal, reanimation candidates flow, diff-check, and model selection (Fable vs OPUS) for skill audit.

**Key decision points:**
- **0-risk duplicate batches** — dated snapshots, all skills active, second snapshot same day → `rm -rf` safe
- **Reanimation candidates** — fuzzy-match archive names against active set → decide: reanimate or delete
- **3-stage pipeline:** md5sum-Diff (local, 0 cost) → Fable 5 (triage, cheap) → OPUS 4.8 (validation, only if needed)

**Verified 2026-07-04:** 2 duplicate batches (302 SKILL.md, 19MB) removed with 0 data loss; 11 reanimation candidates found via fuzzy-match; OPUS 4.8 confirmed Fable's "all dead" claim was false.

---

## Hub-Imported Resolution

When `~/.hermes/skills/hub-imported/` exists — integrate it into the canonical library tree. Hub-imported is a **staging area**, not a permanent home.

→ See `references/hub-resolution.md` for complete protocol: inventory, frontmatter parsing, duplicate detection, diff comparison, SHA snapshot, deletion, categorization, `diff -r` verification, and post-resolution script.

**11-step protocol:**
1. Inventory
2. Extract `name:` from frontmatter (NOT directory name)
3. Duplicate detection via `name:` field
4. Diff comparison (<10 lines = duplicate, >50 lines = different)
5. Active skill integrity snapshot (BEFORE destructive ops)
6. Delete duplicates from `hub-imported/`
7. Classify unique skills by target category (creative/, media/, etc.)
8. Create target directories + `cp -r` (with `/.` to avoid nesting)
9. `diff -r` verification (bit-identical)
10. Hash comparison (active skills unchanged)
11. Remove `hub-imported/`

**Verified 2026-07-04:** 21 hub-imported skills resolved (13 duplicates deleted, 8 moved). `diff -r` confirmed all 8 copies bit-identical. 13 active SKILL.md hashes unchanged. Zero data loss, zero broken refs.

**When NOT to resolve:** During slim-down sessions (inflates count), without `name:` frontmatter check (false positives), or delegated to subagents (parent-side commands more reliable).

---

## Library Hygiene Scan

Periodic health check beyond just size — catch storage bloat, stale artifacts, and path-hardening issues before they compound.

### 5-Command Audit

```bash
cd ~/.hermes/skills

# 1. Storage footprint
du -sh . && du -sh .archive .curator_backups .hub 2>/dev/null
# Healthy: skills dir <40MB total; overhead (archive + backups + hub) <10MB

# 2. Python bytecode in active skills
find . -not -path '*/.archive/*' -not -path '*/.curator_backups/*' \
  \( -name '__pycache__' -type d -o -name '*.pyc' \) 2>/dev/null
# Healthy: 0 results

# 3. Hub index-cache location check
[ -d .hub/index-cache ] && echo "HUB CACHE IN SKILLS: ~/.hermes/skills/.hub/index-cache"
[ -d ~/.hermes/cache/hub-index ] && echo "HUB CACHE OUTSIDE: ~/.hermes/cache/hub-index"
# Healthy: cache is OUTSIDE skills dir

# 4. Curator backup retention
ls -1dt .curator_backups/*/ 2>/dev/null | tail -n +4
# Healthy: nothing listed (max 3 retained)

# 5. Archive recursion (nested hub/backups inside .archive)
ls .archive/_skills-mirror-snapshot/.hub .archive/_skills-mirror-snapshot/.curator_backups 2>/dev/null
# Healthy: 0 results — no nested overhead
```

**When to ignore:** Hardcoded paths are intentionally didactic; archive recursion is known pattern (tar includes live state).

---

## Provenance Integrity

Every `~/.hermes/skills/` has a `.bundled_manifest` (or `.bundled_manifest.sha256`) — the canonical hash manifest for verifying that no skill has been silently modified.

### When to regenerate

- After ANY library mutation: new skill installed, skill patched/updated, skill archived, hub-import resolved
- After curator run
- On suspicion of tamper or unintended drift
- As part of monthly library hygiene

### Regenerate (SHA-256)

```bash
cd ~/.hermes/skills
find . -name SKILL.md \
  -not -path './.archive/*' -not -path './.curator_backups/*' -not -path './.hub/*' \
  -print0 |
while IFS read -r -d '' f; do
  printf '%s:%s\n' "$(dirname "$f" | sed 's|^\./||')" "$(sha256sum "$f" | cut -d' ' -f1)"
done | sort > .bundled_manifest.sha256
```

**Interpretation:**
- 100% match = 🟩 Clean
- 90-99% match = 🟨 Moderate drift
- <90% match = 🟧 Stale manifest
- 0% match = 🟥 Manifest completely out of date → immediate regenerate required

### Key Pitfalls

**Pitfall #32** — Manifest regeneration after batch ops (regenerate AFTER last destructive op, not before)

**Pitfall #33** — Storage overhead from .hub + .curator_backups grows invisibly (active skills should be ~60-70% of total disk usage)

**Pitfall #34** — Shell scripts without executable bit break `./script.sh` calls (fix: `find ... -path "*/scripts/*.sh" | xargs -I{} chmod +x {}`)

**Pitfall #35** — Manifest orphan drift from renamed/removed skills (update old→new names, remove truly-gone entries)

**Pitfall #36** — `.bundled_manifest.sha256` vs actual skills misalignment (regenerate SHA to match manifest count)

**Pitfall #37** — Bundle-Skill type error. Skills without `references/` or `scripts/` dirs MUST NOT reference paths inside those dirs. When a skill was slimmed and all content was moved into the SKILL.md body, remaining `references/X.md` pointers are dead — delete them. Do NOT keep the ref "just in case" the directory is created later. The cleanest bundle-skill is a self-contained SKILL.md with zero external refs.

---

## Cross-Domain Skill Linking

Library hygiene isn't just about **size** — it's also about **discoverability**. Skills in domain clusters (gaming/, devops/, mlops/) should cross-reference relevant method skills (orchestration/, software-development/).

### When to add cross-references

| Condition | Action |
|---|---|
| Domain skill describes a workflow that uses subagents | Add ref to `multi-agent-pitfalls-cheatsheet` + `multi-agent-orchestration` |
| Domain skill mentions parallel research or code audit | Add ref to `research-orchestration` or `subagent-driven-development` |
| Domain skill references a meta-navigator | Add ref to `skill-navigator` |
| Method skill lists domain-specific use-cases | Add refs back to relevant domain skills |
| Adding a new domain skill to the library | Include a `## 🧭 Related Skills` section |

### When NOT to add

- Don't link every skill to every other skill (only concrete workflow benefit)
- Don't add cross-refs to frontmatter's `related_skills` field (that's for programmatic discovery)
- Don't put cross-refs near the top of SKILL.md (append at end)
- Don't link domain→domain cross-refs (covered by cluster co-location)

### Format template

```markdown
## 🧭 Related Skills (Cross-Cluster Navigation)

Skills that support this [domain] cluster but live elsewhere:

- **`skill-navigator`** (orchestration/) — Meta-Navigator. Load FIRST when deciding which skill applies.
- **`multi-agent-pitfalls-cheatsheet`** (orchestration/) — TRIGGER-WATCHLIST for `delegate_task` calls.
- **`multi-agent-orchestration`** (orchestration/) — The 3-Expert Research PATTERN.
```

**Verified 2026-07-02:** 4 GreyHack skills + 3 orchestration skills linked, 6 cross-refs added, matrix verified.

---

## Common Pitfalls

→ See `references/pitfalls.md` for all 31 numbered pitfalls with full details and verification examples.

**Top 5 critical pitfalls:**

1. **Modifying frontmatter during slim-down** — Always instruct: "YAML frontmatter stays EXACT as-is."
2. **Creating references/ files that are too small** — Merge small extractions; <500 bytes is wasteful.
3. **Forgetting to add pointers in SKILL.md** — After extraction, link to each new reference file.
4. **Not excluding archives from the scan** — `.archive/` and `duplicates*` inflate scan results.
5. **Delegating without target size** — State concrete KB target: "Target: SKILL.md ≤12KB."

**Other key pitfalls:**
- #10: Dangling references — CREATE the file, don't delete the link
- #12: First write always overshoots — plan for 2-3 iterative trim-down rounds
- #15: >5 skills need Multi-Wave Pattern (not single-batch)
- #16: Subagent can leave broken refs silently — verify post-wave, don't trust summary
- #17: Re-scan between rounds — top-N candidates change after each slim-down
- #24: `head -1` confirms presence, PyYAML confirms it PARSES (different checks)
- #26: Read actual source code before extracting technical details (SKILL.md paraphrases are not source-of-truth)
- #27: Compression tactics — table conversion, row folding, layer prefix-coding
- #31: Active-skill integrity snapshot — SHA256 before, not after (forensic baseline)

---

## Verification Checklist

### Health Audit Phase
- [ ] **Health audit triggered? Run 10-dimension scan first** (frontmatter, permissions, broken links, secrets, duplicates, manifest, SHA, storage)
- [ ] **Proactive fix stance applied?** Non-security findings fixed immediately; security findings → read-only → user approval
- [ ] **Broken refs categorised?** Run `python3 scripts/broken-ref-scanner.py` — each ref tagged BUNDLE_MISSING / FILE_MISSING / TEMPLATE_PLACEHOLDER
- [ ] **P0 bundle-skills fixed?** Skills with BUNDLE_MISSING >=3 had all dead refs removed from SKILL.md
- [ ] **Shell scripts +x verified** — `chmod +x` on all `*/scripts/*.sh` in active skills (Pitfall #34)
- [ ] **Manifest orphans resolved** — rename old → new names, remove truly-gone entries (Pitfall #35)
- [ ] **SHA manifest aligned** — `.bundled_manifest.sha256` entries match `.bundled_manifest` count (Pitfall #36)
- [ ] **Backups written** — `.bundled_manifest.bak` + `.bundled_manifest.sha256.bak` before destructive operations
- [ ] **Report written** to `~/docs/system/skills-audit-YYYY-MM-DD.md`

### Slim-Down Phase
- [ ] Size scan completed (all SKILL.md files ranked by size)
- [ ] Archives and duplicates excluded from scan
- [ ] `multi-agent-pitfalls-cheatsheet` excluded from scan (see Pitfall #18)
- [ ] Each oversized skill categorized (Monolith / Partial / OK)
- [ ] **For code-documenting skills: source files read before extraction** (see Pitfall #26)
- [ ] Slim-down delegated or executed with explicit target sizes
- [ ] Post-slim-down: frontmatter STARTS with `---` (presence check via `head -1`)
- [ ] **Post-slim-down: frontmatter PARSES as YAML** — round-trip with `yaml.safe_load` confirms all expected keys intact (see Pitfall #24)
- [ ] Post-slim-down: SKILL.md ≤ target size (allow 3% overshoot for small candidates)
- [ ] Post-slim-down: reference files exist and have substantive content
- [ ] SKILL.md contains one-line pointers to each new reference file
- [ ] Post-slim-down: NO dangling `references/X.md` links (bare path or full markdown form)
- [ ] **Compression tactics applied where appropriate** (see Pitfall #27)
- [ ] Master report written to `~/docs/system/skill-slim-down-DATE.md` with before/after table
- [ ] Optional: Patch `multi-agent-pitfalls-cheatsheet` with new patterns discovered this round