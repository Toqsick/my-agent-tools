---
name: skill-duplicate-audit
description: >-
  Use when user asks for scanning the skill library for duplicate scripts, finding stale production copies after a bundle import, choosing a canonical script owner, or removing byte-identical skill assets safely. NOT for reviewing merely similar prose or general frontmatter linting. Classifies production versus archive duplicates, remaps paths, preserves the canonical owner, and verifies cleanup.
version: 1.0.0
author: Hermes
metadata:
  hermes:
    tags:
    - audit
    - skills
    - maintenance
    - de-duplication
    agent: Verifier
    routing_hint: Find byte-identical scripts across skills — duplicate code = drift risk. Run before major skill refactors.
license: MIT
trigger_keywords: ['skill', 'production', 'canonical', 'owner', 'user']
keywords: ['skill', 'production', 'canonical', 'owner', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

# Skill Duplicate Audit

**Purpose:** Find byte-identical scripts across the Hermes skill library (`~/.hermes/skills/`). Duplicate code creates **drift risk**: when the canonical owner improves a script, the duplicates silently fall behind.

## When to Use

- Before major skill refactors (catch hidden dependencies on duplicates)
- During quarterly skill maintenance (H1 2026 audit found 8 production duplicates)
- After pulling a skill bundle (bundles often re-create duplicates of existing skills)
- When debugging weird behavior (skill might be loading a stale duplicate)

## Prerequisites

- Python 3.11+ with `pathlib` + `hashlib` (stdlib only, no install)
- Read access to `~/.hermes/skills/` (Hermes-internal)

## How to Run

```bash
python3 ~/.hermes/skills/meta/skill-duplicate-audit/scripts/find_skill_duplicates.py
```

The script:
1. Walks `~/.hermes/skills/**/scripts/*.py` **including** `.archive/` subdirectories
2. Computes MD5 hash per file
3. Groups files by hash
4. Reports groups with 2+ files (duplicates)

**Known Bug:** The script reports paths using only the first-level category (e.g., `creative/scripts/health_check.py` instead of `creative/comfyui/scripts/health_check.py`). Always verify real paths with `find`.

Exit code: 0 always (advisory only, doesn't modify anything).

## Programmatic Output Parsing

When calling the script from Python, `subprocess.run` with `text=True` can silently return empty stdout (UTF-8 encoding issue). Use binary mode instead:

```python
import re, subprocess
res = subprocess.run(["python3", "~/.hermes/skills/meta/skill-duplicate-audit/scripts/find_skill_duplicates.py"],
                     capture_output=True)
out = res.stdout.decode("utf-8", errors="replace")
groups, cur = [], None
for line in out.splitlines():
    if re.match(r"^MD5:", line):
        if cur is not None: groups.append(cur)
        cur = []
    elif re.match(r"^\s*-\s+\S", line):
        cur.append(line.strip()[2:])
if cur is not None: groups.append(cur)
# Then filter: prod_groups = [g for g in groups if any(".archive/" not in x for x in g)]
```

## Quick Reference

| Output | Meaning |
|---|---|
| `=== No skill-script duplicates found ===` | All clear, no duplicates found |
| `=== Found N duplicate script group(s) ===` | N groups of identical scripts (incl. `.archive`) |

## Procedure

### 1. Discovery Run

```bash
python3 ~/.hermes/skills/meta/skill-duplicate-audit/scripts/find_skill_duplicates.py
```

Note the count and group hashes.

### 2. Parse & Filter: Production vs Archive

The script lumps all files together — archives appear in the same output. After parsing:

```python
prod_groups = [g for g in all_groups if any(".archive/" not in x for x in g)]
archive_only = [g for g in all_groups if all(".archive/" in x for x in g)]
```

Mirror-snapshot archives (`_skills-mirror-snapshot/.archive/`) cause 10+ false duplicate groups — check if the mirror is still active before chasing them.

### 3. Remap Paths (Bug Workaround)

The script reports paths as `{category}/scripts/{name}.py` using only the **first-level** path component. For nested skills (e.g., `creative/comfyui/scripts/health_check.py`), it reports `creative/scripts/health_check.py` — silently dropping the subcategory. Always verify with:

```bash
find ~/.hermes/skills -name "health_check.py"
```

### 4. Identify Canonical Owner

For each duplicate group, find which skill references the script in its `SKILL.md`:
- Run `grep -r "script_name.py" ~/.hermes/skills/ --include="*.md"`
- The skill that references the script is the **canonical owner**
- Duplicates without references are likely accidental copies → safe to delete

### 5. Decision Tree

| Pattern | Action |
|---|---|
| 2+ skills reference the script | **Keep all** (intentional design) or refactor to shared lib |
| Only 1 skill references it | **Delete duplicates** in other skills |
| No skill references it | **Investigate**: orphan script? Recently moved? Safe to delete? |
| All in `.archive/` | **Ignore** (archives are intentional) |
| Mirror-snapshot archive (`_skills-mirror-snapshot/.archive/`) | **Verify if mirror is maintained** — if stale, delete entire mirror dir (creates 10+ false production-dup groups) |

### 6. Delete Duplicates

After identifying the canonical owner:

```bash
# Backup first (defensive)
mkdir -p /tmp/skill-dedup-backup
cp /path/to/duplicate.py /tmp/skill-dedup-backup/

# Remove duplicate
rm /path/to/duplicate.py

# Verify canonical owner still has it
ls /path/to/canonical/owner/scripts/
```

### 7. Re-Run Audit

```bash
python3 ~/.hermes/skills/meta/skill-duplicate-audit/scripts/find_skill_duplicates.py
```

Confirm `Production-Duplikate: 0`.

## Pitfalls

- **Md5 vs Content-Equality**: Two scripts with same MD5 are byte-identical but might have different **intent** (e.g., one is a wrapper, one is the lib). Always check SKILL.md references.
- **Hardcoded Paths**: Many scripts reference `.claude/skills/<name>/...` paths that may be wrong after refactors. If you find duplicates, check both are functional before deleting.
- **Permission Drift**: Duplicates often have different permissions than the canonical (e.g., one is `+x`, one is not). Verify the canonical is executable.
- **Archive Directory**: The script does NOT skip `.archive/` despite walking `**/scripts/*.py` — archive files appear mixed with production files in the output. Filter downstream.
- **Path Reporting Bug**: The script reports paths like `creative/scripts/file.py` when the real path is `creative/comfyui/scripts/file.py` (drops intermediate subcategories). Always verify with `find`.
- **Output Parsing Encoding**: Calling with `subprocess.run(text=True)` can silently return empty stdout. Use binary mode + `.decode("utf-8")` instead.
- **Mirror-Snapshot Duplicates**: The `.archive/_skills-mirror-snapshot/` directory creates 10+ identical-by-content groups that look like production duplicates. Check if the mirror is still maintained before chasing them.

## Verification

After cleanup, run:
```bash
python3 ~/.hermes/skills/meta/skill-duplicate-audit/scripts/find_skill_duplicates.py
```

Expected: `Production-Duplikate: 0` (or only intentional shared lib cases).

## What this Audit Caught

### 2026-07-16 (Overlap & Schwarm-Audit)

Second audit — **MD5 + TF-IDF functional-overlap analysis.**

**Script duplicates:** 29 MD5 groups found (11 with production copies, 18 archive-only).

**Root cause (11 production dups):** `.archive/_skills-mirror-snapshot/` directory duplicating `comfyui/` scripts 3x across archive subdirs. Each file has 1 production copy + 3 mirror copies.

**Archive-only (18 groups):** `_init__.py` (4x), `setup.py`, `gws_bridge.py`, `_hermes_home.py`, `verify_subagent_claims.py`, `search_arxiv.py`, `upload.py`, `critic-gate-ollama.py`, `extract_pymupdf.py`, `extract_marker.py`, `pixel_art.py`, `pixel_art_video.py`, `palettes.py`, `clean.py`, `add_slide.py`, `cc-search.py`, `fetch_transcript.py`, `google_api.py`.

**Functional-overlap findings (TF-IDF cosine on SKILL.md descriptions):**

| Cosine | Pair | Verdict |
|---|---|---|
| 0.622 | `claude-code` ↔ `codex` | Template-identical, tool-name-only diff |
| 0.551 | `copilot-cli` ↔ `codex` | Same template, different CLI name |
| 0.537 | `media-tools` ↔ `youtube-content` | Aggregator duplicates its sub-skill |
| 0.525 | `claude-perf-tuner` ↔ `claude-security-auditor` | Same workstation-toolkit scope |
| 0.385 | `security-audit` ↔ `host-security-audit` | Both Linux security baselines |
| 0.382 | `claude-code` ↔ `blackbox` | Same delegation template variant |

**Recommendations:**
- **P0:** Collapse 5 coding-agent-CLI skills → 1 generic skill + thin wrappers
- **P0:** Merge 4 security-audit skills → 1 Zorin-specific + 1 generic cross-ref
- **P1:** Merge TikTok design pair, media-tools/youtube hierarchy, orchestration plan/sub-sub pair
- **P2:** Consolidate 4 swarm-dispatch skills under one hub

### 2026-07-15 (First Audit)

8 production duplicates removed:
- `validate_analysis.py` (voice-clone → drama-soundtrack owns it)
- `validate_poster_brief.py` (image-remix → dynamic-poster owns it)
- `draft_inspector.py`, `asset_search.py`, `jy_wrapper.py` (creative/video → media/clip-export owns them)
- `beat_detect.py`, `energy_analyze.py`, `render_soundtrack_preview.py` (creative/audio → media/{beat-sync,drama-soundtrack} own them)

Total: ~50 KB duplicate code eliminated. Future drift risk avoided.

## Reference Files

- [`references/functional-overlap-analysis.md`](references/functional-overlap-analysis.md) — TF-IDF cosine methodology for detecting semantic duplicates (skills with different content but same intent). Run this as the second pass after MD5 dedup.