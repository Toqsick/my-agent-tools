---
name: stl-printables-research
author: Yuno
version: 1.0.0
description: |
  Use when systematically finding, verifying, and curating 3D-print STL files from printables repositories, scoring a candidate set, or building a vetted STL library for a project.
  NOT for designing parametric OpenSCAD from scratch (use parametric-3d-printing), printing settings, or slicer config.
  Find, verify, and curate STL files for 3D printing with a systematic scoring pipeline.
  files from multiple platforms.
category: research
full_name: STL / Printables Research Workflow
trigger: user asks for STL candidates / printable model recommendations / MakerWorld
  research / Printables curation / "find me STLs for <X>"
license: MIT
trigger_keywords: ['files', 'printing', 'scoring', 'parametric', 'systematically']
keywords: ['files', 'printing', 'scoring', 'parametric', 'systematically']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['parametric-3d-printing']
---

# STL / Printables Research Workflow

Use this skill when you need to find community-validated 3D print models
(STLs) for a specific printer, category, or use case — especially across
MakerWorld and Printables. This is a **research and curation** workflow,
not a design workflow.

## Prerequisites

- `web_search` + `web_extract` tools available
- Target printer's build volume known (e.g. Bambu Lab A1 Mini: 256×256×256 mm)
- (Optional) `subagent-url-verification-gate` for third-party URL pre-checks

## Workflow

### 1. Query formulation

Search each platform separately for maximal coverage. Typical query patterns:

| Pattern | Example |
|---------|---------|
| Platform + category + object | `MakerWorld PS5 controller stand popular` |
| Platform + object + STL | `Printables headphone stand STL` |
| Platform + popularity sort | `Printables stream deck mount most popular` |
| Compatibility qualifier | `A1 mini`, `no supports`, `print in place` |
| Time qualifier | `2024`, `2025` |

Collect **4–6 candidates per category** (you'll drop some after verification).

### 2. Candidate gathering

For each candidate, capture:
- Title
- Platform URL
- Designer name
- Approximate popularity (likes, downloads — from search snippet)
- Any snippets mentioning target printer / build plate compatibility

### 3. Verification (critical)

**Always verify via `web_extract`, never trust search results alone.**
Search results are metadata-only and frequently truncate/round numbers.
Full page extraction reveals real download counts, comments, and compatibility notes.

Checklist for each extracted model page:

- [ ] Download count, like/boost count, rating value
- [ ] Explicit build volume / printer compatibility notes in description
- [ ] Print profile tabs — does designer include a profile for your printer?
- [ ] Dead link? If web_extract returns 404 or redirect → flag and skip
- [ ] Explicit incompatibility warning? (e.g. "not printable on A1 Mini")
- [ ] Comments section for recurring quality issues (fit problems, warping reports)

### 4. Priority ranking

Prefer models with:

1. **Official print profile** for the target printer in designer's profile list
   (best signal of tested compatibility)
2. **Multiple print profiles** across printer types — signals active maintenance
3. **Rating ≥ 4.7 ★**
4. **High download:like ratio** — active community, fewer drive-by boosts
5. **Recent upload** (< 12 months from current date)
6. **"No supports"** or **"easy print"** in description
7. **Creative Commons BY** license (more permissive than Standard Digital File)

### 5. Fallback handling

When a candidate fails verification:

- **404/redirect** → substitute from search pool immediately
- **Too large for build volume** → look for multi-part version or skip
- **Comments show systematic fit issues** (e.g. "USB-C doesn't fit" × 4 users) → flag in output, demote or skip
- **Reddit link** blocked by web_extract → note in output, rely on primary platform

### 6. Output structure

Deliver findings as structured tables, one per category:

| # | URL | Title | Downloads | Rating | Year | Source | Compatibility |
|---|-----|-------|-----------|--------|------|--------|---------------|

Append a **VERIFIED INDEX** listing all confirmed candidates with verification
status. Add a **Notes** section for dead links, substitutions, and caveats.

## Pitfalls

- **Search result metadata is NOT verified data.** MakerWorld search results
  often show rounded download counts or omit key info. Always extract the
  full page.
- **Printables model IDs change** when models are merged or migrated. A model
  that existed 6 months ago may 404 today. Ratify everything.
- **A1 Mini compatibility is subtle.** Some descriptions say "A1 Mini compatible"
  but the profile only fits the full A1 (256 mm bed × 256 mm). Look for the
  **explicit A1 Mini profile tag** in the Bambu Studio print profile tabs.
- **Download counts are stale signals.** A 2021 model with 5k downloads may
  have fit issues with modern hardware revisions (USB-C shape changes, etc.).
  Check comments for recent feedback.
- **Reddit blocks most scrapers** via web_extract. Rely on MakerWorld/Printables
  primary sources; use Reddit only for sentiment and corroboration.
- **License matters.** Standard Digital File License restricts commercial use
  and redistribution. Creative Commons BY is more permissive. Flag which
  applies in output.

## Related skills

- `parametric-3d-printing` — designing your own parametric OpenSCAD models
  (complementary: research existing STLs first, then fill gaps with design)
- `firecrawl-web` — alternative web extraction for stubborn URLs
- `subagent-url-verification-gate` — generic URL pre-verification pattern

## Support files

- `references/a1-mini-gaming-setup-2026-07-16.md` — concrete example of this
  workflow applied to a gaming-setup STL research task for the A1 Mini
