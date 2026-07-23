---
name: wiki-scout-ingest
description: >-
  Use when user asks for ingesting many sources into an LLM wiki, parallelizing wiki creation across multiple domains, pre-seeding wiki skeletons before worker fan-out, or cross-linking an Obsidian or research corpus. NOT for editing one wiki page or generic vault cleanup without source ingestion. Coordinates reconnaissance, domain scouts, race detection, Queen synthesis, link repair, and verification for large Karpathy-style wikis.
version: 1.5.0
author: Yuno
license: MIT
platforms:
  - linux
  - macos
agent: Researcher
metadata:
  hermes:
    tags: ['wiki', 'orchestration', 'ingest', 'scout-swarm', 'knowledge-base']
    category: orchestration
    related_skills: ['llm-wiki', 'queen-bee-schwarm-dispatch', 'multi-agent-orchestration']
routing_hint: |
  Triggers when: user asks to "feed the wiki", "ingest material", or "populate
  the knowledge base" from existing documents (Obsidian vault, MOCs, research files).
  Use this skill before llm-wiki's standard single-agent ingest when the material
  spans 5+ sources or 2+ domains.
trigger_keywords: ['wiki', 'wiki-scout-ingest', 'ingesting', 'many', 'sources']
keywords: ['wiki', 'user', 'asks', 'ingesting', 'many']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['wiki-ingest-pipeline', 'wiki-corpus-lint-runner', 'context-engineering-kb']
---

# Wiki Scout-Ingest

> Orchestrated multi-agent ingest pattern for populating an LLM wiki from
> existing source material (Obsidian vaults, MOC files, research documents,
> architecture reviews, memory, skills).

## When This Skill Activates

Use this skill when:
- The user wants to **feed** / **populate** / **ingest** a wiki from existing material
- The material spans **5+ sources** or **2+ domains** (e.g., AI/ML + Orchestration + Personal)
- The material is structured as MOCs (Maps of Content) in an Obsidian vault
- You can parallelise the work across subagents per domain

Do NOT use for:
- Single-source ingest (use `llm-wiki`'s standard Ingest operation)
- Query / lookup (use `llm-wiki`'s Query operation)
- One-page research (just use standard tools)

## Prerequisites

1. Wiki exists at `$WIKI_PATH` or `~/wiki` with schema, index, and log
2. Sources identified: Obsidian MOC paths, research file paths, memory recall
3. SCHEMA.md conventions read (tags, frontmatter, domains)

## Workflow: Multi-Agent (5+ sources, 2+ domains)

### Phase 1 — Recon (Queen scouting)

One agent call. Scan what we have and assess scope:

```bash
# Required reads
cat ~/wiki/SCHEMA.md       # conventions + tag taxonomy
cat ~/wiki/index.md         # existing pages + page count

# Source identification
# - Obsidian vault MOCs: find ~/Dokumente/Obsidian\\ Vault/ -name "MOC*" -o -name "*Research*"
# - Research files: locate in ~/30-Library/
# - Memory: mnemosyne_recall
# - Skills: scan ~/.hermes/skills/ for relevant patterns
```

**Key discovery — check for concatenated doc files first:**
Before crawling individual pages of a documentation set, check if the site
offers a single concatenated file — often at patterns like:
- `/docs/llms-full.txt` (Hermes Agent, many LLM-served doc sites)
- `/docs/llms.txt` (common convention for "ingest me into your wiki")
- A "Download all" link on the doc index
- A `/docs/_sitemap` or `/docs/changelog` that links all pages

Use `web_extract` on the root doc URL before dispatching scouts. A single
3MB concatenated file replaces 180 individual `web_extract` calls and gives
each scout a clean chunk with section context intact.

**Output:** Source list per domain + estimated page count.

### Phase 2 — Dispatch (Scout swarm)

Use `delegate_task` with N parallel tasks (one per domain).
Each scout is a `role='leaf'` subagent that:

1. Reads sources for its domain
2. Follows SCHEMA conventions (frontmatter, tags, wikilinks)
3. Writes pages directly to `~/wiki/entities/`, `~/wiki/concepts/`, etc.
4. Copies raw source files to `~/wiki/raw/articles/` or `~/wiki/raw/papers/`
   (see Raw Article Pipeline below for sha256-verification detail)
5. **Does NOT** update index.md or log.md (queen handles merge)

**Critical context to pass each scout:**
- Wiki path and SCHEMA rules
- List of source files/paths to read
- Domain tag to use
- "Write wiki pages, not descriptions — the filesystem IS the deliverable"
- "Antworte auf Deutsch" (when user prefers German)

### Phase 3 — Queen Synthesis (concurrent with Phase 2)

While scouts work, the queen **pre-seeds skeletons** — pages that scouts will
link to via `[[wikilinks]]`. This guarantees no broken wikilinks in scout output.

**Multi-Wave Sequencing (for 10+ expected pages):**

When the ingest is large enough (15+ pages expected across 3+ domains), do NOT
dispatch all material in one shot. Sequence by priority:

```
Wave 1 (P0) — Core tri-domain: 3-4 scouts, one per domain
  ↓ Queen merges, lints, learns
Wave 2 (P1) — Secondary sources: 2-3 scouts, deeper material
  ↓ Queen merges, lints, applies Wave-1 learnings
Wave 3 (P2) — Tertiary / niche sources / deferred material
  ↓
Wave 4 — Lint + consolidate + final report
```

**Why sequence instead of one-shot:**

- Wave 1 reveals **what goes wrong** (slug format, missing entities, wrong
  tags) BEFORE Wave 2 starts — so Wave 2 briefings can be refined
- You catch **scope creep** early (if Wave 1 already produces 35 pages, don't
  dispatch all of Wave 2 — re-evaluate)
- **Lint-pass after each wave** prevents broken-link cascades across waves
- **Wall-Time vs. Quality trade-off:** 4 waves cost ~10% more wall-time but
  deliver 99%+ link coverage vs. often below 80% for one-shot

**Skeleton pre-seeding** (same regardless of wave strategy):

- `_meta/cross-domain/*.md` — bridging concepts
- `comparisons/*.md` — comparative pages
- `_meta/lint-checklist.md` — quality gate
- `_meta/agent-readme.md` — next-session onboarding

Each skeleton: YAML frontmatter + ≥2 outbound wikilinks + stub body.
Skeleton pages use `confidence: medium` (will be updated by scouts).

Also: update index.md (cross-domain + meta sections) and log.md.
Do NOT duplicate cross-domain pages into individual domain sections.

### Phase 3a — Content-File Race Detection (Critical)

**Parallel subagents can overwrite wiki CONTENT pages, not just index.md/log.md.**
In one session, a sibling subagent overwrote a 224-line / 9576-byte concept page
with a 1305-byte stub (just frontmatter, no body content). This was discovered
because the file was suspiciously small and had only basic frontmatter after the
re-read. Unlike index.md/log.md races, there is NO automated warning — the file
write succeeds silently.

**Detection loop during merge (before quality gate):**

```bash
# 1. Re-check every page the queen / this agent wrote
for p in concepts/hermes-v7-skill-format.md; do
    lines=$(wc -l < "$p")
    bytes=$(stat -c %s "$p")
    # Expected sizes per page — if one is suspiciously small, re-read
    echo "  ${lines}L / ${bytes}B : $p"
done

# 2. For pages that look too small: re-read and compare to expected
read_file(path="concepts/hermes-v7-skill-format.md")
# If the body is just frontmatter + stub text → sibling overwrote it

# 3. Recovery: rewrite the substantive content using current file state
# as a fresh anchor (do NOT try to patch the overwritten stub — the
# sibling's version is the canonical current file, you must replace it)
```

**Recovery pattern:**
- Re-read the file to confirm overwrite
- Do NOT attempt `patch` — the sibling's content is the new base, not yours
- Re-create the full page with `write_file` (no `patch` — you're replacing wholesale)
- After the re-write, verify: `wc -l` and `grep -c "\[\["` to confirm substance returned
- Update no other files — the sibling's consolidation already updated index/log

**Prevention:**
- When deploying parallel single-agent work (not multi-agent scout-swarm but
  multiple main-agent instantiations), add a **20-second jitter** before
  content writes to reduce the collision window
- Check `stat --format='%W %Y %n' <path>` before and after your write
  (%W = birth time, %Y = mod time — if they differ, another agent touched it)
- Prefer **disjoint filename namespaces** across sibling agents, especially
  when targeting the same domain or concept directory

### Phase 4 — Merge

After all scouts complete:

1. **Content-file race check** — run Phase 3a detection before anything else
2. **Verify exists** — `find ~/wiki -type f -name "*.md" | sort | wc -l`
3. **Domain distribution** — count pages per domain (e.g., ai-ml: 25,
   orchestration: 6, personal: 9). Report this in the final summary — it gives
   the user immediate insight into coverage balance
4. **Quality gate loop** — run shell verification (see Quality Gate Verification below)
5. **Deduplicate** — search for overlapping entities across domains
6. **Index sync** — add any orphan pages scouts wrote but didn't index
7. **Log consolidation** — single log entry listing all created/updated files
8. **Count update** — bump Total pages in index.md header
9. **Spec compliance check** (optional — when the user references authoritative
   docs for the wiki format, e.g., an official SKILL.md reference):

   - Compare the wiki against the spec's required structure (files, dirs,
     frontmatter completeness, sha256 integrity, tag taxonomy, lint rates)
   - Compute pass rate as `passed/total * 100`
   - Apply actionable fixes (missing frontmatter, broken wikilinks, missing
     sha256 hashes) before reporting
   - Separate genuine issues from deliberate exceptions (inline `[[wikilinks]]`
     in SCHEMA.md/log.md that serve as code examples, oversized pages kept
     intact for internal structure). Log both categories.
   - 90%+ is production-worthy; 95%+ excellent; don't chase 100%
   - Log the compliance result to log.md

   See `references/spec-compliance-pass-2026-07-17.md` for a worked example
   against the official Hermes LLM-Wiki v2.1.0 spec.

10. **Report** — structured summary to user: pages per domain, changes, gaps,
   compliance rate (if spec check was run)

### Phase 5 — Git-Init (Post-Merge)

**Karpathy's explicit recommendation:** "The wiki is just a git repo of markdown
files. You get version history, branching, and collaboration for free."
Initialize the wiki as a git repo if it isn't already:

```bash
cd ~/wiki
git init
git add -A
git commit -m "wiki: initialize at v0.1.0

First commit after initial structure creation and initial ingest.
Source: [user-provided sources]
Pages: N content pages, M raw articles"
```

Create a `.gitignore`:

```bash
cat > ~/wiki/.gitignore << 'EOF'
# Wiki .gitignore
tmp/
cache/
*.swp
*.swo
.DS_Store
EOF
```

**Commit discipline:**
- One commit per major ingest (not per-file — batch at the wave/phase level)
- Include the source URL(s) and page delta in the commit message
- Co-author the source when appropriate (e.g., `Co-Authored-By: Hermes Agent Docs <url>`)
- Use `git log --oneline` to show version history to the user

### Phase 6 — Karpathy Alignment Checklist (Optional)

When the user references Karpathy's original Gist, runs this checklist.
The wiki should:

- [ ] **Is just a git repo of markdown files** — git init done, `.gitignore` exists
- [ ] **Has a `SCHEMA.md`** defining conventions (structure, tags, frontmatter)
- [ ] **Has an `index.md`** with sectioned content catalog and total page count
- [ ] **Has a `log.md`** — chronological, append-only action log
- [ ] **Raw/ is immutable** — sources have `sha256:` frontmatter, never modified
- [ ] **Every content page has YAML frontmatter** (title, created, updated, type, tags)
- [ ] **Every page has ≥2 outbound `[[wikilinks]]`** — no isolated pages
- [ ] **Lint pass passes at ≥95%** — 782 wikilinks with 0 broken is achievable
- [ ] **Tags come from the SCHEMA.md taxonomy** — no tag sprawl
- [ ] **Contradictions handled explicitly** — `contested: true` + `contradictions:` frontmatter
- [ ] **Confidence signals present** — especially `confidence: low` or `medium` on single-source pages
- [ ] **Provenance markers** — `^[raw/articles/source.md]` on synthesis paragraphs
- [ ] **Pages are scannable** — most pages readable in 30 seconds; split >200-line pages
- [ ] **Vanvevar Bush's Memex** is acknowledged as the historical predecessor
  (Karpathy mentions this — a small `_meta/history.md` or a section in the pattern page suffices)
- [ ] **The Karpathy Gist is saved** as `raw/articles/karpathy-llm-wiki-gist.md` with the original
  URL in `source_url:` and the sha256 of the body

When any check fails, fix it before reporting completion.

---

## Workflow: Single-Agent (≤6 sources, 1-2 domains)

When the ingest is small enough that multi-agent dispatch overhead doesn't pay
off, do the work inline. Same phases, single agent does everything.

### Phase 1 — Recon (same as multi-agent)

Read SCHEMA.md, index.md, source files. Assess scope.

### Phase 2 — Raw Article Pipeline

**This is the critical first step.** Before writing any wiki pages, create
immutable raw copies of every source:

1. **Read source** (Obsidian note, research file, memory output, etc.)
2. **Strip Obsidian frontmatter** — source files from Obsidian vault have YAML
   frontmatter that belongs to the vault's metadata model, not the wiki.
   Remove it before computing the body hash. If the source has no frontmatter,
   the body IS the raw file verbatim.
3. **Compute sha256** — over the **body only** (everything after the closing `---`
   of the source's original frontmatter, or the whole file if none).
   Use a Python script for clean separation:
   ```python
   import hashlib, yaml, sys
   with open(sys.argv[1], 'r') as f:
       content = f.read()
   # Strip vault frontmatter if present
   if content.startswith('---'):
       parts = content.split('---', 2)
       if len(parts) >= 3:
           body = parts[2].strip()
       else:
           body = content
   else:
       body = content
   sha = hashlib.sha256(body.encode()).hexdigest()
   print(sha[:12])
   ```
4. **Wrap with wiki frontmatter** — add `title`, `source_url: local://obsidian`,
   `ingested: YYYY-MM-DD`, `sha256` prefix
5. **Write to raw/articles/** — `~/wiki/raw/articles/<source-slug>.md`
6. **Verify** — re-read the file, extract body, hash, compare to original sha256

> **⚠️ Double-frontmatter caveat:** When the SOURCE file itself has YAML frontmatter
> (e.g., a SKILL.md that starts with `---`), the raw article will contain TWO `---`
> blocks: the wiki wrapping frontmatter AND the source's original frontmatter.
> The body for sha256 verification is ONLY the source content **after** the second
> `---` block (the source's original frontmatter is NOT part of the body hash).
> The `verify-ingest.py` script handles this correctly (it uses `split('---', 2)`),
> but if verifying manually, use `tail -n +6` to skip wiki frontmatter (5 lines)
> and extract the body for hashing. Never use `rfind('---')` — it will pick the
> wrong boundary if the source content contains horizontal rules.

### Phase 3 — Wiki Page Creation

Distill from raw articles into wiki pages:

1. **Entities first** — each distinct system/tool/model gets its own page
2. **Concepts second** — abstract patterns and architectures
3. **Cross-domain last** — bridge concepts across domains (write to `_meta/cross-domain/`)

**Per-page rules:**
- YAML frontmatter: `title`, `created`, `updated`, `type`, `domain`, `tags`, `sources`
- ≥2 outbound `[[wikilinks]]` per page
- `sources:` list references raw article paths (e.g., `raw/articles/moc-ki-architektur.md`)
- `confidence:` high (multiple sources) / medium (single source) / low (opinion/fast-moving)
- `contested: true` if sources disagree
- Provenance markers `^[raw/articles/...]` on synthesis statements in body

### Phase 4 — Quality Gate Verification

After writing ALL pages, run a systematic verification loop.

**Preferred approach — reusable Python script:**

```bash
cd ~/wiki
python3 scripts/verify-ingest.py
```

The script (`scripts/verify-ingest.py`) checks all quality gates in one pass:
frontmatter completeness, wikilink resolution (three-way fallback: stem →
slugified-stem → title → slugified-title), source-hash integrity, index/log
inclusion, and page-size warnings. Exit code 0 = pass.

**Fallback — shell-based (when Python unavailable):**

```bash
cd ~/wiki

# 1. Count wikilinks per page
for f in entities/*.md concepts/*.md; do
    count=$(grep -oE '\\[\\[[^]]+\\]\\]' "$f" | wc -l)
    echo "$count wikilinks : $f"
done

# 2. Frontmatter completeness
for f in entities/*.md concepts/*.md; do
    has_title=$(head -10 "$f" | grep -c "^title:")
    has_type=$(head -10 "$f" | grep -c "^type:")
    has_domain=$(head -15 "$f" | grep -c "^domain:")
    echo "$f  title=$has_title  type=$has_type  domain=$has_domain"
done

# 3. Count total pages
find ~/wiki -type f -name "*.md" | wc -l
```

**Three-way wikilink resolution strategy:**

When the verification script checks `[[wikilinks]]`, it doesn't just compare
against filename stems. It builds a resolvable index with four entries per page:

1. `filename.stem` — the filesystem slug (e.g. `qwen-3-5-9b-alibaba-qwen-team`)
2. `slugify(filename.stem)` — in case the stem already has hyphens
3. `raw title from frontmatter` — the human-readable title
4. `slugify(raw title)` — normalised title (handles dots, parens, colons)

This catches mismatches between what an agent writes as `[[qwen-3.5-9b]]`
and what the filesystem created (`qwen-3-5-9b-alibaba-qwen-team`). Without
this fallback, every dot in a model name produces a false-positive lint error.

Update index.md with new pages, log.md with ingest record.

---

## Pitfalls

- **Scout self-report is NOT verified fact** — a scout that says "file written"
  may have written to a wrong path. Always verify with `find` after dispatch.
- **Skeleton timing** — create skeletons BEFORE dispatching scouts, not after.
  Scouts start writing immediately and link to skeletons. If skeletons don't
  exist yet, wikilinks break.
- **Log.md / index.md race** — multiple scouts touching these simultaneously
  corrupts them. Queen writes them in Phase 4 only.
- **Sibling-agent race (MAIN AGENT is not immune)** — even the main agent that
  dispatched the scouts can collide with **parallel sibling subagents** writing
  to the same index.md or log.md at the same time. All wiki-ingest agents,
  regardless of parentage, target these two files. The `patch` tool returns a
  warning `"...was modified by sibling subagent <id>..."` when this happens.
  **Defensive write strategy:**
  1. On `patch` failure with sibling-agent warning, **do not retry blindly**
  2. Re-read the file from disk (the sibling may have already added your content)
  3. Re-evaluate: does my update still need to happen, or was it superseded?
  4. Only re-patch with a fresh `old_string` based on the current file state
  5. For log.md: appends-to-top are **safe** even during races (the warning is
     advisory, the patch may have succeeded). Log writes that failed should be
     re-attempted with current content as `old_string`.
  6. For index.md: full-section replacements are **fragile** during races.
     Prefer targeted single-line insertions near the relevant section header.
- **Content-file overwrite (sibling race variant 3)** — a sibling subagent may
  overwrite a wiki **content page** you created (not index.md/log.md) with a
  stub or different version. Unlike index.md races, there is NO automated
  warning — the write succeeds silently. **Detection:** check each page's
  file size during merge Phase 3a — a page that was 9500+ bytes suddenly at
  1300 bytes is a red flag. Re-read to confirm, then re-create with `write_file`.
  See Phase 3a above for full recovery procedure.
- **Duplicate entities across domains** — same concept can appear in ai-ml AND
  orchestration. Deduplicate via `_meta/cross-domain/` references.
- **Scout skill blindness** — scouts don't auto-load skills. Pass instructions
  in `context`: "Load skill X via skill_view(name='X') before writing."
- **Large obsidian vaults** — don't ingest every note. Target MOCs + their
  direct wikilink children (1-2 hops deep). Deeper hops = noise.
- **Slug normalization at scale** — when creating 20+ pages programmatically,
  titles with special characters (dots `.`, parentheses `()`, colons `:`,
  commas `,`) produce slug mismatches. An agent writes `[[qwen-3.5-9b]]` (from
  title "Qwen 3.5 9B") but the auto-slugified filename becomes
  `qwen-3-5-9b-alibaba-qwen-team.md`. **Fix:** after each ingest wave, run a
  lint + normalization pass to detect and fix these. Expect 100-150 fixes for
  a 50-page wiki. 98% lint-rate is the target; don't chase 100% because some
  wikilinks in SCHEMA.md and log.md reference wiki-internal concepts or use
  inline `[[wikilinks]]` as prose examples.
- **Lint timing vs. late-arriving scouts** — running lint while sibling scouts
  are still writing produces false negatives: the page count changes under you
  (e.g., 44→50 during a single lint pass). **Defensive strategy:** before
  linting, capture a filesystem snapshot
  (`find ~/wiki -type f -name '*.md' | sort > /tmp/wiki-snapshot.txt`) and
  diff it after lint. If pages appeared mid-lint, re-run lint. Or use
  `process(action='poll')` to verify all scouts landed before starting lint.
- **Domain distribution reporting** — after merging, report pages per domain
  (e.g., "ai-ml: 25, orchestration: 6, personal: 9, cross-domain: 4"). Without
  this breakdown the user (and future agent sessions) can't assess coverage
  balance. Use `grep -r "^domain:" ~/wiki/entities/ ~/wiki/concepts/ |
  sort | uniq -c` for a quick tally.
- **Raw articles without frontmatter** — scouts sometimes write raw articles
  without wiki frontmatter (no `source_url:`, `ingested:`, `sha256:`). This only
  shows up during lint, not during Phase 2-4. Run a catch-up pass that detects
  raw files missing frontmatter (first line is not `---`) and adds it
  retroactively with computed sha256. 7 such files in a 47-raw-file wiki is
  typical; budget one pass for this.
- **Oversized pages >200 lines** — lint flags these as split candidates, but
  splitting loses internal structure (cross-heading references, flow, narrative
  arc). Rule of thumb: keep intact if the page has strong internal structure
  (multiple sections that reference each other). Split if it is a flat
  list/bullet dump or if a single section dominates more than 60% of the page.
  Log the deliberate decision in log.md so future lints do not re-flag it.
- **Tag taxonomy churn after spec compliance** — when adding tags to the taxonomy
  (e.g., expanding from 19 to 60 tags to match the official spec), also
  (a) retroactively add the new tag to any page that semantically fits it,
  (b) add it to SCHEMA.md taxonomy list, (c) update tag counts in index.md.
  Re-lint after the churn to catch pages whose tags are now valid.
- **HTTP 429 rate-limit recovery (delegation-level)** — a subagent that hits
  `HTTP 429: Usage limit reached for N hour` is NOT a mission failure — it's a
  transient provider-limit error. Recovery procedure:
  1. Check which topics the *other* (non-429) scouts already covered
  2. Identify gaps: list all expected topics vs. what arrived
  3. Write missing topics manually (Queen-direct) — the 429 scout ran in
     parallel with other waves, so most content may already exist
  4. For the remaining gaps: re-dispatch to a *different* model/provider
     (not the same one that rate-limited) OR write inline
  5. Log the 429 event + the recovery method + any gaps that remain
  6. Never re-dispatch to the same provider immediately — the clock resets
     per-provider, not globally
  **Validated 2026-07-17:** Cluster B (Hermes-Docs Features + Skills) hit a
  5h-usage-limit. Recovery found 8/9 topics covered by sibling waves + 1
  Lückenfüller `context-files-and-personality.md` written Queen-direct.
- **Out-of-order async batch completion** — when multiple delegation waves run
  simultaneously (e.g., Waves 1-4), they complete IN THE ORDER THEY FINISH,
  not in the order they were dispatched. Wave 3 (607s runtime) can arrive
  BEFORE Wave 1 (1981s runtime). This means:
  1. The late-arriving batch's sibling agents have been modifying `index.md`,
     `log.md`, and content pages in your absence
  2. **Always re-read shared files before editing them** after an async batch
     arrives — do NOT assume the file state you cached is current
  3. When the late arrival report says `NOTE: subagent modified files the parent
     previously read — re-read before editing`, do exactly that
  4. If the late arrival's findings are already consolidated by earlier waves,
     run a diff-comparison (page counts, domain distribution) — no re-work needed
  5. The late batch's log entry should acknowledge the consolidation state,
     not repeat work already logged
  **Validated 2026-07-17:** Wave 1 (1981s) arrived after Waves 3+4 (607s+845s)
  were complete. Wiki state unchanged — all Scout-Outputs already integrated.
- **False-positive lint results for convention references** — wikilinks like
  `[[readme]]`, `[[schema]]`, `[[license]]` or `[[index]]` in wiki pages that
  reference wiki-level convention files (README.md, SCHEMA.md in the wiki root)
  are NOT broken links — they resolve correctly in Obsidian because the target
  files exist at the wiki root but outside the standard /entities/ /concepts/
  tree. **Mitigation:**
  1. Filter these convention references in your lint script: match against a
     hardcoded allowlist eg. `["readme", "schema", "license", "index", "changelog", "log", "contributing"]`
  2. In the lint report, note `N false-positives (convention refs — resolved by Obsidian)`
     rather than `N broken links`
  3. 99.8% lint-pass after filtering is acceptable — don't chase 100% when the
     remaining "broken" links are all convention refs
  **Validated 2026-07-17:** 1239 wikilinks across 174 content pages, 2
  false-positive (readme, schema) — lint score 99.8% after filtering.
- **Entity deletion triggers cross-reference repair** — deleting a wiki entity
  page (merge into umbrella, replace by several focused pages) leaves broken
  wikilinks across the entire wiki. Do NOT delete the file and assume lint will
  catch it. The fix is systematic:
  1. `grep -rn '\[\[old-slug' --include='*.md' . | grep -v 'raw/'`
  2. Classify each: direct link, link-with-alias, self-reference (page itself)
  3. Build a canonical remap: `old_link → (new_target, new_display)`
  4. Batch-patch all affected content files in one round (not one-by-one)
  5. Re-run `scripts/verify-ingest.py` to confirm zero broken links remain
  6. Log the merge rationale in log.md (which entity, why, how many files patched)
  See `references/cross-reference-repair-pattern.md` for the full procedure.

## Related Skills

- `llm-wiki` — the wiki itself (use for single-source ingest, query, lint)
- `queen-bee-schwarm-dispatch` — the underlying orchestration pattern
- `obsidian` — reading/managing the Obsidian vault
- `multi-agent-orchestration` — general subagent orchestration patterns

## Reference Files

- `references/scout-swarm-walkthrough.md` — full recipe from an earlier tri-domain ingest session
- `references/single-agent-ingest-recipe.md` — concrete recipe for a 6-source/16-page single-agent pass (alternative to scout swarm for small ingests)
- `references/sibling-agent-race.md` — concrete transcript + defensive write strategy for index.md/log.md collisions during parallel ingest
- `references/multi-wave-ingest-worked-example-2026-07-17.md` — hard-numbered 4-wave ingest at scale (100 files, 330 wikilinks, 98.8% lint)
- `references/hermes-docs-5-scout-ingest-worked-example.md` — hard-numbered 5-scout parallel ingest of 3MB/180-page Hermes Agent Docs (131 pages, 782 wikilinks, 100% lint-pass)
- `references/cross-reference-repair-pattern.md` — systematic multi-file patching procedure after entity merge/delete (2026-07-17)
- `templates/lint-checklist.md` — quality gate template
- `templates/agent-readme.md` — next-session onboarding template
- `scripts/verify-ingest.py` — reusable Python verification script (frontmatter, wikilinks, sha256, index/log coverage)

## Example: 3-Scout Tri-Domain Ingest

```yaml
tasks:
  - goal: "Ingest AI/ML sources from MOC KI-Architektur"
    context: "SCHEMA rules, domain=ai-ml, tags from taxonomy"
  - goal: "Ingest Orchestration sources from MOC Lernen & Orchestration"
    context: "SCHEMA rules, domain=orchestration, tags from taxonomy"
  - goal: "Ingest Personal Knowledge from MOC Home / Daily Notes"
    context: "SCHEMA rules, domain=personal, tags from taxonomy"
```
