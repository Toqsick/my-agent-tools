---
name: wiki-ingest-pipeline
description: "Use when user asks to grow a Karpathy-style LLM Wiki through batch source ingest, parallel domain scouts, cross-domain synthesis, slug resolution, broken-link repair, or compliance self-audit. NOT for a single-source wiki update or generic multi-agent research. Orchestrates a scalable ingest pipeline while preserving canonical links, frontmatter, tags, and schema alignment."
version: 1.4.0
author: Yuno
license: MIT
platforms:
  - linux
  - macos
metadata:
  hermes:
    tags: ['wiki', 'knowledge-base', 'research', 'ingestion', 'scaling']
    category: research
    related_skills: ['llm-wiki', 'obsidian', 'queen-bee-orchestration']
agent: Researcher
routing_hint: |
  Agent scope: Wiki population, bulk ingest, lint-mass-repair, compliance
  auditing against the llm-wiki skill spec. Off-scope: single-source ingest
  (delegate to `llm-wiki`), Obsidian vault operations (`obsidian` skill).
  Routing spec: `yuno-team-routing`.
trigger_keywords: ['wiki', 'source', 'ingest', 'domain', 'user']
keywords: ['wiki', 'source', 'ingest', 'domain', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['wiki-scout-ingest', 'llm-wiki']
---

# Wiki Ingest Pipeline

Seed and maintain a Karpathy-style LLM wiki at scale. This skill extends
the `llm-wiki` skill's single-source ingest into a parallel, orchestrated
pipeline that can take a fresh wiki from 0 to 50+ pages in one session.

## Division of Labor

| Skill | Scope |
|---|---|
| `llm-wiki` | Architecture setup, single-source ingest, query answering, basic lint |
| **`wiki-ingest-pipeline`** | Parallel batch ingest, slug resolution at scale, compliance audit, Karpathy alignment |

> **Run `llm-wiki` first** to read SCHEMA + index + log before **this skill**
> activates the pipeline. Orientation is always step 0.

## When This Skill Activates

Use this when the user:

- Has multiple diverse sources to ingest at once (Obsidian exports, Perplexity
  collections, memory dumps, web bookmarks, arXiv exports)
- Wants to **seed a fresh wiki from scratch** with existing knowledge
- Has a wiki with hundreds of wikilinks showing broken-link sprawl
- Asks "does the wiki conform to the spec?" or "how aligned is it with Karpathy?"
- Has a wiki that needs a **slug normalization pass** (dots/special chars in links
  that don't resolve to filesystem slugs)

Do NOT activate for single-source ingest, routine query, or orienting to an
existing wiki — those belong to `llm-wiki` for LLM-content ingest, or
use `references/perplexity-artifact-sequential-ingest.md` **within this
skill** when the source is a live codebase / Perplexity repo artifact
(server code, package.json, SKILL.md with verbatim code extraction).

## Pre-Flight Checklist

Before any parallel work, run:

1. **Read SCHEMA + index + log** (delegate to `llm-wiki` orientation)
2. **Survey sources:** scan directories, collect file lists, note domain coverage
3. **Check disk space:** `df -h /` — wikis grow fast. 50 raw articles * 15 KB each
   is invisible; 50 synthesis pages * 3 KB each plus link-fix passes is also
   invisible. But the ingest run itself can spike context. The constraint is
   your context window, not the filesystem.
4. **Classify sources into domains** matching SCHEMA's taxonomy:
   - AI/ML → entities, concepts
   - Personal/Yuno → concepts, cross-domain
   - Orchestration → comparisons, _meta/cross-domain
5. **Decide on strategy:**
   - <10 sources → sequential (delegate to `llm-wiki` ingest per source)
   - 10-50 sources → **parallel domain scouts** (this skill)
   - 50+ sources with overlap → **phase 1: discovery scouts, phase 2: synthesis**
6. **Set `todo`** with clear milestones so you don't lose tracking across
   parallel subagent output returning out of order
7. **Verify source content vs task brief** — When a brief lists expected pages
   or sections (e.g., "cron-jobs, delegation, kanban, goals"), verify the
   actual source files contain those topics BEFORE deploying scouts. A brief
   may describe a cluster's expected shape while the actual source covers
   something entirely different.
   ```bash
   grep -c "cron\|webhook\|delegate\|kanban" "$SOURCE_FILE" 2>/dev/null || echo "FILE NOT FOUND"
   ```
   If the brief claims content the source lacks, document the discrepancy in
   `log.md` and adjust scope. Don't deploy scouts on unverified assumptions
   — you'll waste subagent context and create orphan stubs.

## Pipeline: Parallel Domain Scouts (Queen-Bee Pattern)

This is the core pattern. It differs from `llm-wiki`'s "bulk ingest" by
running **independent domain scouts in parallel** that each own their slice
of the wiki.

### Step 1: Triage sources into batches

```markdown
- **Domain A: AI/ML** — 15 files (model reviews, MoE tuning, VRAM budgets)
- **Domain B: Orchestration** — 12 files (Hermes-V7, multi-agent patterns)
- **Domain C: Personal/Yuno** — 8 files (memory dumps, yuno-cleaner, skills)
- **Cross-Domain** — 5 files (architecture comparisons, framework research)
```

Each batch should be 5–15 sources for one subagent. Too few (<5) wastes
agent overhead; too many (>15) blows the subagent's context.

### Step 2: Deploy parallel scouts via `delegate_task`

```python
# Pseudocode for orchestration
tasks = [
    {"goal": "...scout AI/ML domain... create/update pages in concepts/ and entities/...",
     "context": "SCHEMA rules: tags from taxonomy, frontmatter required, min 2 wikilinks..."},
    {"goal": "...scout Orchestration domain... create/update pages in comparisons/ and concepts/...",
     "context": "Same SCHEMA rules. Cross-reference AI/ML entities when found."},
    {"goal": "...scout Personal/Yuno domain... create pages in concepts/ and _meta/cross-domain/...",
     "context": "Same SCHEMA rules."},
]
delegate_task(tasks=tasks, role="leaf")
# Returns: array of {summary, files_created, files_updated, warnings}
```

**Critical context to pass each scout:**
- Wiki path (absolute)
- SCHEMA rules (frontmatter, taxonomy, min 2 wikilinks, confidence markers)
- Domain scope (which directories to write to)
- Existing pages (so they don't create duplicates — copy relevant index entries)
- `_meta/` directory exists — cross-domain pages go there

### Step 3: Consolidate scout output

Scouts return their work as summaries. Collect:

```python
all_created = []
all_updated = []
all_warnings = []
for result in scout_results:
    all_created.extend(result.get("files_created", []))
    all_updated.extend(result.get("files_updated", []))
    all_warnings.extend(result.get("warnings", []))
```

Then:

1. **Re-read `index.md`** (a sibling may have edited it while scouts ran)
2. **Update `index.md`** — add all new pages under correct sections
3. **Update `log.md`** — one entry for the batch with file lists
4. **Run lint** (see below) — expect broken links because scouts may have
   referenced entities from other domains
5. **Broken-link sweep** (see Slug Resolution below)

> ⚠️ **Sibling race condition**: `index.md` and `log.md` are shared state.
> Read immediately before writing, not at the start of this phase.
> See [[#Sibling-Subagent Race Conditions on index.md (Critical)]] for
> detection, repair, and prevention patterns.

### Step 4: Cross-domain synthesis pass

After all domain pages exist, create cross-domain pages in `_meta/`:

- Pages that bridge 2+ domains (e.g., `queen-bee-pattern` references both
  Orchestration patterns and personal workflow)
- The `llm-wiki-pattern.md` page documenting the wiki pattern itself
- Any comparison that draws from multiple domains

**One agent pass** (you, not a subagent) — cross-domain synthesis needs
the full picture.

## Slug Resolution (Critical Path)

This is the #1 scaling challenge. Page titles with dots, numbers, or
special chars produce different slugs than expected:

| Wikilink | Expected Slug | Real Slug (from filesystem) |
|---|---|---|
| `[[qwen-3.5-9b]]` | `qwen-3-5-9b` | `qwen3-5-9b-alibaba-qwen-team` |
| `[[Ornith 1.0 9B]]` | `ornith-1-0-9b` | `ornith-1-0-9b-deepreinforce-ai` |
| `[[schema]]` | `schema` | `wiki-schema` (Title: "Wiki Schema") |

### Strategy: Shrink-Before-Expand

**NEVER rename files first.** Renaming breaks every existing wikilink to that
file *and* creates duplicates if a page with the new name already exists.

Instead:

1. **Count broken links** — `re.findall(r'\[\[([^\]\|]+?)(?:\|[^\]]+)?\]\]', text)`,
   normalize each to slug, check against filesystem slugs
2. **Identify the canonical slug** — the filesystem stem IS the slug.
   `qwen3-5-9b-alibaba-qwen-team` is the truth, not `qwen-3.5-9b`.
3. **Fix wikilinks in content** — replace `[[qwen-3.5-9b]]` with
   `[[qwen3-5-9b-alibaba-qwen-team]]` across ALL files. Use sed or
   patch with replace_all=true when the pattern appears many times.
4. **Run lint to verify** — every fixed link now resolves.
5. **Only then rename files** — if you must (e.g., a file slug is genuinely
   wrong like `multi-agent-frameworks-2026-07` where the date doesn't belong).
   Rename with `mv old.md new.md`, then fix ALL cross-references to the old
   name in the same commit.

### Dedicated slug-resolution pass

When the wiki has 100+ broken links from slug mismatches:

```python
# Step 1: Build multi-form slug map
# CRITICAL: file stems with dots/special chars produce DIFFERENT
# normalized forms than their raw stem. Both must be in the set.
slugs = set()
for p in Path(wiki).rglob("*.md"):
    if "raw/" in p.parts: continue
    slugs.add(p.stem)                                                   # raw stem: "qwen-3.5-9b"
    slugs.add(re.sub(r"[^\w]+", "-", p.stem.lower()).strip("-"))        # slugified: "qwen-3-5-9b"
# Step 2: Build title→slug map from frontmatter (title-slug form)
for p in pages:
    m = re.search(r"^title:\s*(.+)", p.read_text(), re.M)
    if m:
        ts = re.sub(r"[^\w]+", "-", m.group(1).lower()).strip("-")
        slugs.add(ts)                                                   # title-slug: "qwen3-5-9b-alibaba-qwen-team"
        title_slugs[ts] = p.stem
# Step 3: Scan ALL files for [[links]] that don't resolve
# Strip code fences first so inline examples don't inflate the count
# Strip frontmatter slug: lines too (they're config, not wikilinks)
# Step 4: For each broken link, look up in title_slugs map
# Step 5: If found, replace in-place with canonical file stem
```

## Compliance Self-Audit

After a large ingest pass, run a structured compliance check against the
`llm-wiki` skill's spec to catch regression:

### Checklist

| Check | Pass Condition |
|---|---|
| SCHEMA.md present | File exists with domain, conventions, taxonomy |
| index.md present | File exists with sectioned structure |
| log.md present | File exists with chronological entries |
| Every page has frontmatter | title, created, updated, type, tags, sources |
| All tags in taxonomy | No tag appears on a page that isn't in SCHEMA.md |
| `raw/` files have sha256 | Every raw article has `sha256:` in frontmatter |
| No broken wikilinks | Every `[[link]]` resolves to an existing file (code-fence aware) |
| Min 2 outbound wikilinks | Every content page links to 2+ other pages |
| No pages >200 lines | Flag oversized (split candidates, not must-split) |
| `confidence` on opinion-heavy | Single-source pages should NOT default to `confidence: high` |
| Contradictions handled | Pages with conflicting claims have `contradictions:` set |
| `_meta/` pages not in index | Cross-domain pages ONLY linked from index header, not body sections |
| Git repo initialized | `git rev-parse HEAD` succeeds |
| Log size | Under 500 entries; rotate if exceeded |

### Procedure

```bash
WIKI="<wiki_path>"

# Count files
find "$WIKI" -name "*.md" -not -path "*/raw/*" | wc -l

# Frontmatter scan — every .md (except raw/ and log) starts with ---
for f in $(find "$WIKI" -name "*.md" -not -path "*/raw/*"); do
    head -1 "$f" | grep -q "^---" || echo "NO FRONT: $f"
done

# Tag audit — extract all tags from all pages, compare to SCHEMA's taxonomy
grep -rh "^tags:" "$WIKI" --include="*.md" | sort -u

# Wikilink lint — code-fence aware, raw/-excluded
python3 -c "
import re, sys
from pathlib import Path
w = Path('$WIKI')
slugs = {p.stem for p in w.rglob('*.md') if 'raw/' not in p.parts}
for p in w.rglob('*.md'):
    if 'raw/' in p.parts: continue
    t = re.sub(r'\x60\x60\x60.*?\x60\x60\x60', '', p.read_text(), flags=re.S)
    for m in re.finditer(r'\[\[([^\]\|]+?)(?:\|[^\]]+)?\]\]', t):
        s = re.sub(r'[^\w]+', '-', m.group(1).strip().lower()).strip('-')
        if s not in slugs: print(f'BROKEN: {p.relative_to(w)} -> {m.group(0)}')
"

### Body-Hash Computation Caveat

When verifying `sha256` on raw articles, the hash must be computed over the
**body only** (everything after the closing `---` of the YAML frontmatter), not
the entire file. This is critical when the source markdown contains `---`
horizontal rules inside the content — using `rfind('---')` will pick the wrong
boundary.

**Correct approach:** parse frontmatter explicitly:

```python
import yaml, hashlib
with open(path) as f:
    content = f.read()
# Find the SECOND occurrence of --- (closing frontmatter)
lines = content.split('\n')
if lines[0].strip() == '---':
    close_idx = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == '---')
    body = '\n'.join(lines[close_idx+1:])
    sha256 = hashlib.sha256(body.encode()).hexdigest()
```

**Wrong approach:**
```python
# BAD: rfind picks the LAST --- which may be a horizontal rule in the content
body = content[content.rfind('\n---\n')+5:]
```

Verify by comparing the declared hash against the computed body hash, not the
raw file hash.
```

## Karpathy Alignment Checklist

Align your wiki with Andrej Karpathy's original gist
(https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

### Mandatory (Karpathy's core)

- [ ] Wiki is a **git repo** — `git init`, first commit before any content
- [ ] `index.md` sectioned with one-line summaries
- [ ] `log.md` chronological, append-only
- [ ] `SCHEMA.md` conventions file
- [ ] `raw/articles/` for immutable source ingestion
- [ ] `[[wikilinks]]` between pages
- [ ] Every new page added to index immediately
- [ ] Every action logged

### Strongly Recommended

- [ ] **Obsidian-compatible** — frontmatter, wikilinks, folders = works as vault
- [ ] **Confidence/contested markers** in frontmatter (prevents weak claims hardening)
- [ ] **Provenance markers** (`^[raw/articles/source.md]`) on synthesis pages
- [ ] **sha256 on raw files** — drift detection on re-ingest
- [ ] **Karpathy gist stored as raw article** — download the original gist to `raw/articles/karpathy-llm-wiki-gist.md` with sha256 frontmatter. Preserves the original reference spec inside the wiki and prevents scope drift.
- [ ] **git commit after every ingest batch** — versioned knowledge
- [ ] **Search engine** (qmd or BM25) for 100+ source wikis
- [ ] **Conversational-ingest** (agent+user discuss before writing) for
      ambiguous/questionable sources — batch-ingest for bulk

### Nice-to-Have (from gist comments & community)

- [ ] `_meta/cross-domain/` synthesis pages bridging domains
- [ ] Dataview setup (if in Obsidian) for `TABLE tags FROM "entities"`
- [ ] Page-size warning at 200 lines (split candidate)
- [ ] `confidence: low` lint pass — flag weak claims for user review
- [ ] Rotate log.md at 500 entries → `log-YYYY.md`
- [ ] **Per-domain MOC pages** — create `_meta/moc-<domain>.md` pages (e.g., `moc-orchestration.md`, `moc-ai-ml.md`) with sectioned page lists for quick navigation. Essential for wikis with 100+ pages across multiple domains.
- [ ] **`.obsidian/` vault config committed** — configure `app.json` (alwaysUpdateLinks, newLinkFormat=shortest), `appearance.json` (theme, fonts), `core-plugins.json` (16 plugins), and `community-plugins.json` (dataview, templater, excalidraw, obsidian-git). Git-tracked so the vault opens immediately as an Obsidian workspace on any machine.

## Broken-Link Mass Repair Strategy

When lint reveals dozens or hundreds of broken `[[wikilinks]]`, don't fix
one at a time. Use the systematic sweep:

### Phase 1: Classify broken links

| Category | Example | Action |
|---|---|---|
| **Slug mismatch** | `[[qwen-3.5-9b]]` → `qwen3-5-9b-alibaba-qwen-team` | Bulk-replace across all files |
| **Missing stub** | `[[content-pipeline-as-code]]` no file exists | Create stub with frontmatter + backlinks |
| **Inline in code** | `` [[slug]] `` in a code snippet | Escape or wrap in backticks |
| **SCHEMA convention** | `[[schema]]` referring to SCHEMA.md itself | Add SCHEMA.md frontmatter so it has a slug |
| **Legacy name** | Page was renamed, old link persists | Fix link to new name, or create redirect stub |
| **Evolving slug** | Page was renamed to a shorter canonical slug (e.g., `queen-worker-pattern-multi-agent` → `queen-worker-pattern`), old variant persists in cross-references from other ingests | Bulk-replace old variant with the new canonical slug across ALL files |

### Phase 2: Resolve by category

Order matters — fix slugs first (90% of cases), then stubs, then the rest.

```python
# Phase 2a: Fix slug mismatches (bulk replace across ALL files)
fixes = {
    "qwen-3.5-9b": "qwen3-5-9b-alibaba-qwen-team",
    "ornith-1.0-9b": "ornith-1-0-9b-deepreinforce-ai",
}
# Phase 2b: Create stubs for remaining missing entities
# Phase 2c: Fix inline-code conventions
# Phase 2d: Add SCHEMA.md frontmatter if missing
# Phase 2e: Final lint to verify
```

### Phase 3: Verify

```bash
LINT=$(python3 lint-wikilinks.py "$WIKI" 2>/dev/null)
if [ "$LINT" = "0" ]; then echo "100% PASS"; else echo "FIX: $LINT remaining"; fi
```

## Reference Files

| File | Contents |
|---|---|
| `references/slug-resolution-playbook.md` | Worked example of a real slug-resolution pass on a 100-page wiki with 48 broken links. Step-by-step reproduction recipe with Python and shell commands. Read this BEFORE your first slug pass. |
| `references/parallel-ingest-race-incident.md` | Concrete transcript of a real sibling-subagent race during parallel cluster ingest (2026-07-17) — 16-second race window, three stacked race conditions, detection-and-repair transcript. Read this BEFORE your first parallel ingest consolidation. |
| `references/perplexity-artifact-sequential-ingest.md` | Sequential single-source ingest workflow for Perplexity-generated repo artifacts. Use when ingesting 1–3 sources with live codebases (package.json, server.ts, SKILL.md). Includes 6-phase workflow, quality gates, tag-taxonomy verification, and common pitfalls. Alternative to the parallel scout pattern. |
| `references/atomic-write-race-prevention.md` | Worked example of escaping the patch tool entirely for race-safe index/log updates. Full Python code for `atomic_write()`, `curated_count()`, and a combined `update_index`/`update_log` harness. Read this BEFORE your first parallel consolidation when sibling-race warnings appear. |
| `references/phantom-source-detection.md` | Pattern for handling source files referencing external URLs that return HTTP 404 (dead HF models, renamed repos). 4-step workflow: URL verification → deactivated frontmatter → 404-audit article → caveats in synthesis pages. Status codes, confidence cascades, and when-to-use matrix. Read this BEFORE any ingest batch with model references. |
| `references/obsidian-vault-setup.md` | Complete `.obsidian/` vault configuration: app.json, appearance.json, core-plugins.json, community-plugins.json, MOC creation pattern, and `.gitignore` conventions. Read this when setting up a wiki as an Obsidian vault for the first time. |
| `references/repo-wiki-curation-pipeline.md` | End-to-end worked example: turning a GitHub repo into a wiki via local `wiki/`-folder + PR (proved 2026-07-22 on Toqsick/greyscripts, 65 pages, 8 subagents, ~30 min). Includes 5-wave orchestration pattern, briefing templates per wave, naming-convention-table, Queen-Verify 2-pass cross-link validator, and Tier-A/B/C scoping. Read this BEFORE curating a wiki from a GitHub repo. |

## Pitfalls

- **NEVER rename files to match wikilinks** — rename is destructive and
  cascading. Fix the links first, only rename if the slug is genuinely wrong,
  and do both in the same git commit.
- **Don't count broken links in SCHEMA.md** — it uses `[[wikilinks]]` as
  convention documentation, not as real links. Exclude it in lint.
- **Code fences protect inline** — `[[links]]` inside ` ``` ` blocks are
  documentation, not wikilinks. Strip fences before linting.
- **Partial-read → stale patch anchors** — `read_file` with `offset`/`limit`
  returns a partial view. The patch tool warns `"was last read with offset/limit
  pagination (partial view). Re-read the whole file before overwriting it."`
  when you then attempt a patch. Always do a **full read** (`read_file` without
  offset/limit) before any write operation on large shared files like
  `index.md` or `log.md`. When you already read partial, re-read fully before
  the first patch.
- **Subagents have no memory of your wiki** — pass the current index entries
  in context so they don't create duplicates. Without this, you'll get
  `quantization-methods.md` AND `quantization-methods-comparison-q4-q5-q6-q8.md`.
- **Don't deploy >6 parallel scouts** — Hermes delegation caps at 6 concurrent.
  Increase source-per-scout before increasing scout count.
- **Expect slug mismatch after every batch** — it's the normal cost of
  concurrent writes. Budget a slug-resolution pass after every major ingest.
- **`delegate_task` returns self-reports** — verify file creation with
  `ls` or `search_files` before updating index. A scout that says "wrote
  15 files" may have written 12 if 3 conflicted.
- **Filename-collision overwrite (sibling race variant 2)** — A sibling
  subagent may create a STUB file with the exact same filename as your
  substantive page, silently overwriting your content. Detection:
  ```bash
  stat --format='%W %Y %n' wiki/concepts/hermes-telegram-setup.md
  # %W = birth time, %Y = mod time
  # If birth ≠ mod time and mod time is later -> overwritten by sibling
  ```
  Recovery: rewrite the substantive content once, then let the sibling's
  next consolidation commit (which runs after your rewrite) capture the
  correct version. Do NOT recursively fight over the same filename between
  successive patches — you'll both lose content in a race that neither
  wins. Git resolves last-write-wins at the file level; make sure your
  last write is the good one.
- **Write to `raw/` only from `index.md` evaluation** — the sha256 hash
  protects against re-ingests but doesn't alert on silent overwrites.
  Catch this during compliance audit, not during ingest.
- **PHANTOM sources with dead external URLs** — when a source file references
  an external resource (HF model, repo, API) that returns HTTP 404, do NOT
  skip the file. Create the raw article with `status: deactivated` + `reason:`
  frontmatter, and optionally a 404-audit summary article. See
  `references/phantom-source-detection.md` for the full 4-step workflow,
  frontmatter template, confidence-cascade rules, and when-to-use matrix.
- **Frontmatter `slug:` field is NOT a wikilink** — When linting, the `slug:` field in YAML frontmatter looks like a broken wikilink target but is just documentation. Exclude frontmatter lines starting with `slug:` from the wikilink scan, or filter out wikilinks whose text matches a known `slug:` value from existing files.
- **`replace_all=True` as intentional strategy for duplicate wikilink fixes** — When `patch` fails with `"Found 2 matches for old_string"` and both matches are the SAME broken wikilink (e.g., once in body, once in "Verwandte Konzepte"), using `replace_all=True` is the CORRECT response — faster and less fragile than crafting unique context for each occurrence. Only inspect uniqueness when the matches are structurally different (e.g., one is a wikilink and one is plain text that happens to match).
- **GitHub Wiki-Pages are NOT pushable via API/git** (proved 2026-07-22 on Toqsick/greyscripts) — GitHub activates the wiki repo `org/repo.wiki.git` only after the **first page is created via the Web-UI**. `git push` returns "Repository not found" because the repo does not exist yet, and `gh repo create Toqsick/repo.wiki --public` fails with "Name cannot end in .wiki". There is no programmatic workaround through `gh api` or git. **Workaround:** create a local `wiki/` folder in the main repo on a feature branch (`feat/wiki-initial`), commit it, push, and open a PR. Then optionally enable GitHub Pages on `/wiki/` for public access. This is the only path an AI agent can drive end-to-end without Web-UI access. Proven on greyscripts 2026-07-22: 65 pages, 6129 insertions, PR #77 created from `feat/wiki-initial` → `develop`.
- **Landing-Page naming: `Home.md` NOT `INDEX.md`** (proved 2026-07-22 on greyscripts) — Subagents default to `INDEX.md` (matches the user literal wording in the brief). But for a navigable wiki that interlinks with a sidebar, the convention is `Home.md` so every cross-link `[Home](Home)` resolves. After the working-phase, Queen-Verify cross-link sweep must run TWO passes: once with targets stripped of `.md`, once with raw targets, because `[Home](Home.md)` and `[Home](Home)` are both legal Markdown and the validator `pages = {p.stem for p in WIKI.glob('*.md')}` set only contains stem forms. **Detection:** `ls Home.md INDEX.md` — if only INDEX.md exists, rename with `mv INDEX.md Home.md` and run `sed -i 's|(INDEX)|(Home)|g; s|\[INDEX\](INDEX)|[Home](Home)|g'` across sidebar/overview/audit files.
- **Cross-link validator needs `.md`-strip in TWO directions** (proved 2026-07-22 on greyscripts, 7 broken links initially) — The lint regex captures `[text](target)`. Target may be `Home`, `Home.md`, or `./Home`. Validator must strip `.md` from target before checking against `{p.stem for p in WIKI.glob('*.md')}`. Many broken links come from subagents writing `[Home](Home.md)` when `Home.md` is the actual file. **Worked example:** 7 broken links in audit files (`_Audit_Completeness.md → Home`, `_Audit_Lint.md → Tool-build_all` etc.) — fixed with `sed -i 's|\[Home\](Home)|[Home](Home.md)|g; s|Tool-build_all|Tool-build-all|g'` (rename `Home` ↔ `Home.md` and `_` → `-` for tool names). Always run final lint with the 2-pass variant.
- **Tool/Dir naming: underscore → kebab-case during wiki-curation** (proved 2026-07-22 on greyscripts) — Repo source files use underscores (`build_all`, `fix_perms`, `scp_upload`, `smtp_enum`, `wifi_crack`). Wiki pages should use kebab-case for URL stability (`build-all`, `fix-perms`, `scp-upload`, `smtp-enum`, `wifi-crack`). Subagents forget this mapping and write Tool-pages with underscores. **Fix pattern:** at Queen-Verify time, run a single `sed` pass with all underscore→dash mappings across all Tool-*.md files before lint: `sed -i 's|Tool-build_all|Tool-build-all|g; s|Tool-fix_perms|Tool-fix-perms|g; ...' wiki/Tool-*.md wiki/*.md`. Add a "Naming-Convention-Table" to the implementer briefing so the mapping is set BEFORE the wave, not after.

## 5-Wellen Curation-Pattern (for Repo→Wiki flows)

When the goal is to produce 50+ structured pages from an existing GitHub repo (wiki, docs site, knowledge base), the per-task "fresh subagent per task" model does NOT scale. Use this 5-wave architecture instead. Proven 2026-07-22 on Toqsick/greyscripts: 65 pages, 8 subagents, ~30 min, PR #77 created.

```
Wave 0: Setup (Queen only)
  ├─ git clone <repo> to /tmp/<repo>-local
  ├─ Checkout feature branch (or create from develop)
  ├─ Merge necessary refs (develop + main if diverged)
  ├─ Write Home.md (INDEX), _Sidebar.md, _Footer.md
  └─ Commit + push (no PR yet)

Wave 1: Working-Subagents (5 parallel)
  ├─ Subagent A: Tools/<Domain>-X (one page per source file)
  ├─ Subagent B: Patterns/<Category> (one page per category)
  ├─ Subagent C: Docs/<Doc-Name> (one page per repo doc)
  ├─ Subagent D: Development/<Guide-Name>
  └─ Subagent E: Meta/<Page-Name> (Quickstart, Install, Changelog)

Wave 2: Tier-C Sub-Pages (1-2 subagents)
  └─ Subagent F: Detail-Pages for complex items

Wave 3: QA-Subagents (3 parallel)
  ├─ Subagent G: Linter (Em-Dash ≤ 1, En-Dash = 0, Boldface = 0, page-size)
  ├─ Subagent H: Completeness Auditor (vs repo inventory)
  └─ Subagent I: Cross-link Validator (optional — Queen re-runs in Wave 4)

Wave 4: Queen-Verify + Integration (non-delegable)
  ├─ 2-Pass Cross-link validator (see pitfalls above)
  ├─ Naming-convention sed sweep (underscores → kebab-case)
  ├─ Home.md rename if subagent created INDEX.md
  ├─ Write wiki/README.md
  └─ Final commit + push

Wave 5: PR + Verify
  ├─ Push feature branch
  ├─ gh pr create --draft --base develop
  ├─ Verify PR exists via gh api
  └─ Optional: enable GitHub Pages via repo settings
```

**Critical briefing fields for each Wave-1 implementer (do NOT skip):**
- REPO-PFAD + ZIEL-ORDNER (absolute paths)
- Output-naming-mapping table (pre-baked underscore→kebab)
- Page-format skeleton (complete markdown template)
- Cross-link convention: `[Tool-lib-core](Tool-lib-core)` — NO `.md` suffix
- External repo-link convention: full GitHub URL
- Wiki-Stand: fixed date for all pages
- Style rules: Em-Dash ≤ 1, En-Dash = 0, no mid-sentence bold

Full briefing templates + worked example (greyscripts 65-page run): `references/repo-wiki-curation-pipeline.md`.

## Sibling-Subagent Race Conditions on index.md (Critical)

When parallel domain scouts finish and you consolidate into `index.md`,
sibling subagents may be editing the same file simultaneously. This is the
normal cost of parallelism, not a bug — but it requires explicit detection
and repair.

### How the Race Manifests

1. **Your patch lands in a stale location.** You wrote a `patch` with a
   `old_string` that's now non-unique because a sibling inserted content
   nearby. The tool reports `"Found 2 matches for old_string"`.

2. **Your page-count update is wrong.** You read 28, compute 28+7=35, but
   a sibling already bumped it to 123. Now 35 undershoots.

3. **The patch tool warns `"modified by sibling subagent"`.** This is a
   **hard stop signal** — re-read the file before any further edits.

### Detection Loop

Before every `patch` on shared files (`index.md`, `log.md`), check the
response for the sibling-modification warning. If it fires:

```python
# After a patch call returns with the warning
if "sibling subagent" in response.get("_warning", ""):
    current = read_file(path="wiki/index.md")          # re-read
    repair_race_condition(current)                     # fix collaterals
    patch(path="wiki/index.md", old_string=new_anchor, new_string=...)  # retry
```

### Repair Patterns

| Symptom | Detection | Repair |
|---|---|---|
| **Duplicated section** (two `### Concepts` headings in same block) | `grep -c "### Concepts" index.md` > 1 | Remove the second heading. Keep both sets of list entries under the correct heading. |
| **Page count mismatch** | `grep "Total curated pages"` ≠ your count | Re-read the number from current file, compute increment from that. |
| **Entry already present** | `grep " slug" index.md` finds your line | Skip re-adding. Verify and continue. |
| **Entries in wrong section** | Headings shifted | Re-read the full structure, move entries to correct current section. |
| **Whitespace / git-diff failure** | `git diff --check` reports trailing whitespace or blank line at EOF after sibling edited the file | `p.read_text(); p.write_text(s.rstrip() + '\\n')` to normalize EOF; run `git diff --check` again before commit |
| **Post-commit slug mismatch** — sibling committed your files + index.md in a single consolidation commit; `git status` shows clean but index.md wikilink aliases don't match actual filenames | `git show --stat HEAD` reveals sibling's actual filenames; `ls <dir>/<prefix>*` shows actual stems; `grep -oE '\\[\\[[^]]+\\]' index.md | while read l; do slug=$(echo "$l" | sed 's/\\[\\[//'); [ -f \"concepts/$slug.md\" ] || echo \"MISSING: $slug\"; done` | 1. `git show --stat <sibling-sha>` to discover actual filenames the sibling used<br>2. `ls <dir>/<expected-prefix>*` to verify actual file stems<br>3. Cross-reference index.md entries against filesystem; identify each alias that doesn't match its real slug (e.g., `hermes-provider-architecture` in index → file is `hermes-providers-architecture.md`)<br>4. `patch` each wrong index.md alias to the correct slug<br>5. `git diff --check` before committing<br>6. `git commit -m "fix: rename index.md slugs to match actual filenames"`<br>7. Run broken-link lint to confirm 0 remaining |

### Prevention

1. **Read `index.md` immediately before your first patch**, not before the
   consolidation phase. A sibling may have written to it while you were
   creating wiki pages.

2. **One-shot patches.** Instead of: count → section → entries (3 patches),
   batch all changes into the fewest possible patches.

3. **Pre-verify uniqueness.** Before calling patch, run
   `grep -c "old_string" index.md`. If >1, choose a more specific anchor
   with surrounding context lines. If 0, check whitespace/encoding.

4. **Final lint is the safety net.** After all patches, run the compliance
   audit. A 0-broken-links result is proof the race was handled correctly.

5. **Run `git diff --check` before committing.** A sibling may have
   introduced trailing whitespace or blank-line-at-EOF issues. Normalize
   (`p.read_text(); p.write_text(s.rstrip() + '\\n')`) before the commit
   so the diff stays clean.

6. **Escape the patch tool entirely with atomic writes** — when you need
   to update `index.md` or `log.md` in ways that involve counting,
   computation, or multiple insertions, write a **dedicated Python script**
   that reads the file, computes the new content, and writes it atomically
   via `tempfile.mkstemp` + `os.replace`. This bypasses the patch tool's
   shared-file race window entirely because the file is only replaced once,
   and `os.replace` is atomic on Linux (rename(2) on the same filesystem).
   See `references/atomic-write-race-prevention.md` for a worked example.

7. **Count from filesystem, not from memory.** Instead of:
   ```python
   old_count = 60  # stale — sibling may have bumped it
   new_count = old_count + 7  # wrong!
   ```
   Do:
   ```python
   def curated_count() -> int:
       excluded = {"SCHEMA.md", "index.md", "log.md", "README.md"}
       count = 0
       for p in WIKI.rglob("*.md"):
           if "raw" in p.parts or ".git" in p.parts:
               continue
           if p.name in excluded:
               continue
           count += 1
       return count
   ```
   This sidesteps the sibling race on page-count tracking entirely.
   Update the index header with the real count from disk, not an
   increment from a stale cache.
