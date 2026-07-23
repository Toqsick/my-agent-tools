---
name: bulk-readme-to-wiki-pages
description: >-
  Use when the user asks to generate N wiki pages from existing per-tool README files in a repo (e.g. "Erstelle N Tool-Wiki-Pages + 1 Overview"). NOT for editing a single note, writing docs from scratch, or generating docs from source code. Covers prose-count vs verification-count reconciliation, parallel batched write_file, per-page structural template (Übersicht/Verwendung/Funktionen/Build/Hinweise/Verwandte Tools/Quelle), durable style constraints (no em-dashes, no mid-sentence boldface, ISO dates, language), and post-generation verification by file count.
  For vertiefte Detail-Companion-Pages (API-Referenz + 2-3 Code-Beispiele für eine bereits existierende Wiki-Seite) siehe `references/detail-companion-pages.md`.
category: documentation
platforms:
- linux
- macos
- windows
version: 1.1.0
author: Yuno (Basti)
source: session-2026-07-22-greyhack-wiki-generation, session-2026-07-22-tier-c-detail-pages
lane: koenigin
reasoning_effort: high
metadata:
  hermes:
    tags:
    - wiki
    - readme
    - documentation
    - batch-generation
    - repo-docs
    related_skills:
    - quality-gate-runner
    - obsidian-vault-cluster-operations
    - obsidian-subagent-briefing-template
    - multi-agent-orchestration
    - swarm-workspace-isolation
    triggers:
    - wiki pages from readmes
    - repo wiki generation
    - N Tool-Pages erstellen
    - bulk readme to wiki
    - Tools-Overview
    - Detail-Pages
    - API-Referenz
    - Cheat-Sheet
license: MIT
trigger_keywords: ['pages', 'wiki', 'count', 'tool', 'docs']
keywords: ['pages', 'wiki', 'count', 'tool', 'docs']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['wiki-corpus-lint-runner']
---


# Bulk README -> Wiki Page Generator

Class-level skill for the recurring task: **given a repo with N per-tool README files, generate N structured wiki pages + 1 overview page, with specific style and verification constraints.**

This skill does NOT cover:
- Editing a single existing wiki page (use `patch` directly)
- Writing docs from scratch with no README source
- Generating docs from source code comments (-> `codebase-inspection` or repo-specific skills)
- Obsidian-vault fan-out (-> `obsidian-vault-cluster-operations`)
- **Detail-Companion-Pages** (vertiefte API-Referenz + 2-3 Code-Beispiele fuer eine bereits existierende Wiki-Seite) - siehe `references/detail-companion-pages.md`

## Trigger Conditions

Use this skill when the user asks to:
- "Erstelle N Tool-Wiki-Pages + 1 Overview im Repo"
- "Generate wiki pages for all tools in `<repo>/<tools-dir>/`"
- "Convert every README in `<dir>` to a wiki page"
- "Build me N+1 wiki pages from the per-tool READMEs"

A single shared trait: N >= 10 READMEs to convert, all in one repo, with a named style/structure constraint.

## Core Principles

### Principle 1: Trust the verification count, not the prose count

**Problem:** The user writes "35 Tool-Pages" in the prose of the request, but the explicit list at the end of the prompt contains 33 tools, and the verification step also expects `ls Tool-*.md | wc -l` to return 33.

**Symptom:** Agent silently produces 33 (correct, matches the list and verification) and feels unsure whether it underdelivered, OR produces 35 by inventing 2 phantom tools and producing pages with fabricated content.

**Rule:**
1. Read the EXPLICIT list (named items) and count those
2. Read the VERIFICATION command and identify its expected count
3. If prose-count and list-count and verification-count disagree -> **the verification count wins**
4. Note the discrepancy in the final report ("35 im Auftrag, 33 in der expliziten Liste - habe 33 erstellt, da Verification-Step `wc -l` = 33 erwartet")
5. Never invent phantom pages to match prose count

**Why:** The verification command is what the user (or their automated grader) will actually run. Mismatching it is a hard failure. Inventing pages to hit a prose count creates fabricated content - which is one of the worst agent failure modes.

**Fundiert:** Session 2026-07-22 (greyhack-tools wiki): prose said "35", explicit list had 33, verification expected 33. Produced 33 -> verified correct.

### Principle 2: Page Structure Template

Every per-tool wiki page MUST follow this skeleton (order matters, headings in German):

```markdown
# Tool-<kebab-name>

**Quelle:** [<relative path to README>](<github-url-to-README>)
**Datei:** <repo-relative path to .src>
**Status:** <aktiv | WIP | Demo/Research | geplant>
**Stand:** <YYYY-MM-DD>

## Uebersicht           <- 1-3 sentence purpose
## Verwendung         <- minimal usage examples (verbatim from README if possible)
## Funktionen         <- API/ablation features + step-by-step Ablauf when present
## Build-Anleitung    <- from README when present, omit if not
## Hinweise           <- gotchas/pitfalls, often critical for these tools
## Verwandte Tools    <- 3-5 wiki-links to sibling Tool pages
## Quelle              <- original README link + repo path
```

Overview page (`Tools-Overview.md`) MUST have:

```markdown
# Tools-Overview
<provenance header>
## Uebersicht
## Schnellzugriff      <- anchor links to each category
## Core / Exploits / Crypto / Libraries / Utilities / Apps / DevTools / Deployment
   (one table per category: | Name | Beschreibung | Status |)
## Abhaengigkeitsgraph  <- ASCII or list
## Build-Reihenfolge   <- ordered list of which tools depend on which
## Siehe auch
## Quelle
```

### Principle 3: Durable Style Constraints

These constraints are user-imposed and reusable across future sessions:

| Constraint | Reason |
|---|---|
| **No em-dashes or en-dashes** in body text | German convention favors "bis", "und", or simple hyphen "-". Em-dash counts fail style gates. |
| **No mid-sentence boldface** (`**word**` inside a paragraph) | Only headings, table headers, and code identifiers may be bold. Inline emphasis belongs to code or list structure. |
| **No YAML frontmatter** in the page body | Pure Markdown - the wiki renderer expects it. Frontmatter leaks render as visible text. |
| **Stand date in ISO format** (`2026-07-22`) on every page | The user's preferred date convention. |
| **Language: German** for narrative text | Code identifiers, command names, file paths stay in English. |
| **Line limit: <= 200 lines per page** | Renderability and load-time budget. Pages over 200 lines should be split. |
| **Cross-links use relative paths** (`[Tool-x](Tool-x.md)`) | External repo links use full GitHub URLs. |
| **Verwandte Tools section at bottom** with 3-5 links | Bidirectional navigation - overview page lists this page, this page links to siblings. |

### Principle 4: Batch Writing Strategy

For N >= 10 pages, write in batches of 6-8 parallel `write_file` calls per turn. Reasons:

1. Each batch fits a single model response without context bloat
2. Each batch can be partially verified (count + `wc -l`) before the next batch
3. If the session crashes mid-batch, partial progress is still preserved
4. Smaller batches make it easier to fix a single bad page without rewriting the whole batch

**Sequence:**
1. Read all N READMEs in parallel (single turn, N read_file calls)
2. Plan page content from the reads (mental, no tool)
3. Write pages in batches of 6-8 (multiple turns)
4. Verify: `ls Tool-*.md | wc -l` + `wc -l Tool-*.md Tools-Overview.md` for line-limit check
5. Write Tools-Overview.md last (depends on knowing all names)

### Principle 5: Source Discipline

Every per-tool page must link its source README with BOTH:
- A relative path (for repo navigation): `[greyhack-tools/<tool>/README.md]`
- A full GitHub URL (for direct browsing): `(https://github.com/<owner>/<repo>/blob/main/<path>)`

If the source README is short (e.g. only "Migrated from GreyRepo" stubs), the wiki page should still be substantive by:
- Documenting what's KNOWN from the README
- Marking gaps explicitly ("Beschreibung aus README nicht verfuegbar - Migration aus GreyRepo, vollstaendige Doku steht aus")
- Linking to siblings that share the gap (the "stubs migrated from GreyRepo" pattern is shared across many tools)

NEVER invent implementation details to fill out a thin README. Document the thinness, link to the cluster, move on.

## Workflow (5 Phases)

### Phase 1: Inventory + Plan

```bash
# 1. Count source READMEs (terminal)
ls <tools-dir>/*/README.md | wc -l

# 2. Compare to user's stated count
#    User said N, ls says M -> use M
#    User said "35" but ls says 33 -> use 33, note discrepancy

# 3. Confirm output directory exists
ls <wiki-dir>/  # should exist (e.g. INDEX.md, _Sidebar.md already present)
```

Plan the page-naming convention up front:
- Tool name -> kebab-case (snake_case -> kebab-case): `auto_exploit` -> `Tool-auto-exploit`
- README "Kategorie" field -> overview table column
- README "Version" / "Stand" -> page header

### Phase 2: Parallel Read

Read ALL source READMEs in a single turn with parallel `read_file` calls. This saturates the model's context with all sources at once and avoids sequential slow reads.

If the model context budget is tight (>= 30 long READMEs), read in 2-3 batches instead.

### Phase 3: Batched Write

Write pages in batches of 6-8 per turn. Each `write_file` call is independent - the runtime parallelizes them.

**Per-page content rules:**
- Uebersicht: 1-3 sentences from README "Beschreibung" / first paragraph
- Verwendung: copy verbatim code blocks from README "Verwendung" sections
- Funktionen: paraphrase list sections into tables when structure is rich
- Ablauf: copy numbered steps from README when present
- Build-Anleitung: copy from README when present
- Hinweise: copy "Bekannte Probleme" / "Hinweise" sections - these are the highest-value content
- Verwandte Tools: pick 3-5 sibling tools by category adjacency, link via `[Tool-x](Tool-x.md)`

**Batch boundaries:**
- Sort tools alphabetically or by category before batching - keeps related tools together
- Don't split a single tool across batches

### Phase 4: Overview Page Last

After all Tool-*.md are written, write `Tools-Overview.md` because it depends on:
- Knowing all tool names (for the table)
- Knowing all categories (for the section headers)
- Knowing all dependencies (for the graph)

**Overview structure:**
- 7-8 category tables (one per category from the source list)
- Each row: `[Tool-kebab](Tool-kebab) | short desc | status`
- Dependency graph as a list of `lib_core -> dependents` chains
- Build-Reihenfolge as an ordered list (lib_core first, then everything else)

### Phase 5: File-Count + Style Verification

```bash
# 1. File count
ls <wiki-dir>/Tool-*.md | wc -l
# Expected: matches the explicit list count

# 2. Line limits
wc -l <wiki-dir>/Tool-*.md <wiki-dir>/Tools-Overview.md
# Expected: max < 200, mean around 70-90

# 3. Spot-check 2-3 pages with read_file
#    Confirm content matches source README

# 4. Check for style violations
grep -n "—|–" <wiki-dir>/Tool-*.md    # should be empty (no em/en-dash in body)
grep -n '\*\*[^*]*\*\*' <wiki-dir>/Tool-*.md | grep -v '^[^:]*:[0-9]*:#' | grep -v '^[^:]*:[0-9]*:|'
#    inline bold outside tables = violation

# 5. Confirm overview exists + has all tools
ls <wiki-dir>/Tools-Overview.md
```

Report the verification results in the final message:
- "X / X expected Tool pages written"
- "Max line count: N (limit 200)"
- "Mean line count: N"
- "All style checks passed" (or list violations)

### Phase 6: Cross-link + Coverage Audit (REQUIRED for N >= 20 pages)

**Why this phase exists:** Phase 5 (file count + style) confirms pages were
written but does NOT catch three classes of silent breakage:
(a) Wiki pages whose cross-link targets do not exist (broken links)
(b) Repo inventory items that have no wiki page (coverage gaps)
(c) External links (GitHub URLs, marketing sites) that have rotted or point
to nonexistent repo files

**Proven example 2026-07-22:** All 33/33 tool pages existed, but 6 broken
cross-link targets (`Tool-build_all`, `Tool-fix_perms`, `Tool-scp_upload`,
`Tool-smtp_enum`, `Tool-wifi_crack`, `Home`) slipped through into INDEX.md,
_Sidebar.md, and Installation.md because some linkers used `snake_case`
while the rest of the wiki was `kebab-case`. A simple `wc -l` check misses
this entirely.

**6.1 Coverage check (repo inventory vs wiki pages):**

```bash
# Real tools in repo (those with .src code)
for d in <repo>/<tools-dir>/*/; do
  if find "$d" -maxdepth 2 -name "*.src" 2>/dev/null | head -1 | grep -q .; then
    basename "$d"
  fi
done | sort -u

# Wiki pages (normalized to kebab-case)
ls <wiki-dir>/Tool-*.md | sed 's|.*/||;s|\.md$||;s|^Tool-||;s|_|-|g' | sort -u

# Diff: any tool in repo without a wiki page?
comm -23 <(real_tools_sorted) <(wiki_tools_normalized_to_kebab)
```

**Naming normalization rule:** If the source repo uses `snake_case`
(`auto_exploit`, `build_all`, `wifi_crack`) and the wiki convention is
`kebab-case` (`Tool-auto-exploit`, `Tool-build-all`, `Tool-wifi-crack`),
normalize BOTH sides before diffing. Without normalization, every
`snake_case` tool produces a phantom "missing tool" report.

**6.2 Cross-link validation (every internal `[Text](Target)` link):**

```bash
# Extract all wiki cross-link targets
cd <wiki-dir>
grep -ohE '\]\([A-Za-z][A-Za-z0-9_\-]*\)' *.md | sed 's/^](//;s/)$//' | sort -u

# Extract all wiki pages (filenames without .md)
ls *.md | sed 's|.*/||;s|\.md$||' | sort -u

# Diff: targets that don't resolve
comm -23 <(unique_link_targets) <(wiki_pages)

# For each broken target, show which files contain it
while read t; do
  grep -lH "]($t)" *.md
done < broken_targets.txt
```

**Pattern discovered 2026-07-22:** The most common broken-link cause is
**naming-convention drift between files**. When INDEX.md and Sidebar.md are
written by a different pass than the per-tool pages, the linker may use
`Tool-build_all` while the page is `Tool-build-all`. Always validate
Phase 6.2 after every batch write, not just at the end.

**6.3 External link validation:**

```bash
# 1. Internal repo links (github.com/<owner>/<repo>/blob/main/<path>) — verify path exists locally
grep -ohE 'https://github.com/<owner>/<repo>/blob/main/[^)]+' *.md \
  | sed 's|.*/blob/main/||' | sort -u \
  | while read p; do
      [ -f "$p" ] || echo "BROKEN_REPO_PATH: $p"
    done

# 2. External domains - HEAD-request check (skip LAN IPs)
grep -ohE 'https?://[^) ]+' *.md | sed 's/`$//;s/,$//' | sort -u \
  | grep -v 'github.com/<owner>/<repo>' | grep -v '^http://192\.168\.' \
  | while read url; do
      code=$(curl -I -s -o /dev/null -w "%{http_code}" -m 10 "$url" 2>/dev/null)
      [ -n "$code" ] && [ "$code" != "404" ] || echo "BROKEN_EXT: $url ($code)"
    done
```

**Pattern discovered 2026-07-22:** LAN IP addresses (e.g.
`http://192.168.178.92:8765/...`) appear in repo wikis as in-game file
references. These are intentionally non-resolvable from a headless audit
context and should be excluded from the broken-link list with a comment
in the audit report ("16 LAN URLs excluded as in-game network references").

**6.4 Audit report format:**

```markdown
## Coverage Audit

| Check | Verdict | Detail |
|-------|---------|--------|
| Tool-Coverage | PASS | 33/33 (100%) |
| Pattern-Coverage | PASS | 11/11 active verified, 6 category-pages |
| Doc-Coverage | PASS | 11/11 source-docs have wiki-pants |
| Cross-link validation | NEEDS-FIX | N broken targets |
| External links | PASS | 0 broken (M GitHub + N external domains) |

## Broken cross-links (NEEDS-FIX)

| Link target | Resolves? | Appears in |
|-------------|-----------|------------|
| `Tool-build_all` | no (correct: `Tool-build-all`) | INDEX.md:31, _Sidebar.md:33 |
| `Home` | no (correct: `INDEX`) | _Sidebar.md:3 |
| ... | ... | ... |

## Fix commands (one-liner per broken target)

```
sed -i 's/Tool-build_all)/Tool-build-all)/g' wiki/INDEX.md wiki/_Sidebar.md
sed -i 's|\[Home\](Home)|[Home](INDEX)|' wiki/_Sidebar.md
```
```

The audit report should be written to `<wiki-dir>/_Audit_Completeness.md`
(or similar underscored prefix to keep it sortable) for future re-runs.

## Pitfalls

| # | Pitfall | Mitigation |
|---|---|---|
| 1 | Prose says "35" but list says 33 - agent produces 35 by inventing phantom tools | Principle 1: trust the explicit list and verification command |
| 2 | Prose says "35" but list says 33 - agent produces 33 and feels like it underdelivered | Principle 1: note the discrepancy in the final report; verification count wins |
| 3 | Em-dashes leaked into body text | Style constraint table - run em-dash/en-dash check after write, fix before reporting |
| 4 | Mid-sentence boldface used for emphasis | Style constraint table - only headings/table headers/code may be bold |
| 5 | YAML frontmatter accidentally included | Wiki renderer leaks it as text - strip before write |
| 6 | Page > 200 lines because the README was long | Split: move verbose content to "Funktionen" subsections; condense usage examples |
| 7 | Thin README migrated from external source - agent invents tech details to fill out the page | Principle 5: document the thinness, link to siblings, mark "Doku steht aus" |
| 8 | All pages written but overview page forgotten | Phase 4: dedicated overview phase after all Tool-*.md are written |
| 9 | Cross-links broken because kebab-case naming was inconsistent between files | Naming rule: snake_case -> kebab-case consistently; run Phase 6.2 cross-link audit after generation to catch any drift; for snake_case tools always quote the link with the explicit kebab-case target, never let autocomplete default |
| 10 | Verification runs the wrong command | Use glob `Tool-*.md` for tool pages and `Tools-Overview.md` for overview explicitly |
| 11 | Write 33 pages in one massive turn -> context bloat -> later pages lose quality | Batch in 6-8 page chunks (Principle 4) |
| 12 | Source README contains German typos that propagate to the page | Reproduce verbatim from README; do NOT silently fix typos that change semantics |
| 13 | Phase 5 file-count + style checks pass but 6 broken cross-link targets slip through into INDEX/Sidebar/Installation because some files use snake_case while pages use kebab-case | Phase 6 is REQUIRED for N >= 20: run cross-link extraction against wiki-pages set, diff for unresolved targets, fix with sed per target before declaring done. Naming normalization MUST happen on BOTH sides before any coverage diff |
| 14 | Phase 5 reports 100% but external GitHub repo links point to nonexistent files | Phase 6.3: extract every blob/main/<path> URL, sed to local path, test -f each one; report BROKEN_REPO_PATH for any that fail |
| 15 | Wiki audit script reports LAN IPs as broken external links because HEAD-requests can't reach them | These are intentional in-game network references, not real broken links. Exclude with grep filter and document the exclusion in the audit report |
| 16 | Cross-link audit says "Tool-X broken" but Tool-X page exists - the wiki filename uses a different casing/naming than the link target | Wiki link targets are case-sensitive on most renderers. Phase 6.2 must compare the exact link string (not normalized) against the exact filename (not normalized). Only normalize for the coverage diff in Phase 6.1, not the cross-link resolution check |
| 17 | User asks for "Detail-Pages" / "API-Referenz" / "vertiefe bestehende Wiki-Seite X" - agent falls back to standard template because the skill only covers the bulk case | See `references/detail-companion-pages.md`. Detail-Companion-Pages have a distinct skeleton (API-Referenz-Tabelle statt Funktionen-Bullets, nummerierte Code-Beispiele statt eines einzelnen Verwendung-Blocks, expliziter Versionshinweis bei Source/README-Drift) |

## Connecting Skills

- **`quality-gate-runner`** - for markdown style gates after generation (line limits, link integrity, frontmatter checks)
- **`obsidian-vault-cluster-operations`** - same batched-write pattern, but for Obsidian vaults (not repo wikis); share the verification-by-file-count discipline
- **`obsidian-subagent-briefing-template`** - if the task grows beyond 50 pages, dispatch via subagent clusters instead of direct write
- **`multi-agent-orchestration`** - for very large N (>100 pages) where parallel subagents outperform serial writing
- **`swarm-workspace-isolation`** - if subagents are dispatched, scope each subagent to a disjoint slice of tools
- **`wiki-scout-ingest`** - research-side wiki ingestion (different class: external sources, not repo READMEs)
- **`obsidian-vault-quality-audit`** - sibling audit pattern for Obsidian vaults (this skill's Phase 6 is its repo-wiki equivalent)

## Reference Files

| File | Purpose |
|---|---|
| `references/page-template.md` | Verbatim per-tool page template with placeholders - copy and fill per tool |
| `references/overview-template.md` | Verbatim Tools-Overview template - fill after all Tool-*.md exist |
| `references/session-2026-07-22-greyhack-wiki.md` | Worked example: 33 tools + overview from `greyhack-tools/*/README.md` |
| `references/session-2026-07-22-wiki-audit.md` | Worked example: Phase-6-Audit-Output (cross-link + coverage + external-link) |
| `references/detail-companion-pages.md` | **Detail-Companion-Pages-Erweiterung** - vertiefte API-Referenz + nummerierte Code-Beispiele fuer Tier-C-Tools, Patterns-QuickRef, Tools-CheatSheet. Wird geladen wenn "Detail-Pages", "API-Referenz", "Cheat-Sheet", "vertiefe bestehende Wiki-Seite X" gefragt ist. |

## Source

- Session 2026-07-22: Generated 33 Tool pages + 1 Tools-Overview from `greyhack-tools/*/README.md` in greyscripts repo
- Session 2026-07-22 (Tier-C-Detail-Pass): Generated 5 Detail-Companion-Pages (`Tool-lib-core-Detail`, `Tool-grsa-Detail`, `Tool-portscan-Detail`, `Patterns-QuickRef`, `Tools-CheatSheet`) for already-existing wiki pages
- Constraints enforced: no em/en-dash, no mid-sentence boldface, no YAML, line limit 200, ISO date, German, kebab-case naming, source provenance on every page
