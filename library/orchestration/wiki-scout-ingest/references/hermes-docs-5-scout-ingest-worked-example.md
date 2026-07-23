# Hermes-Agent-Docs 5-Scout Parallel Ingest — Worked Example (2026-07-17)

> Session date: 2026-07-17 | Model: deepseek/deepseek-v4-flash
> Source: https://hermes-agent.nousresearch.com/docs/llms-full.txt
> Result: 70→131 content pages, 199 files, 782 wikilinks (100% lint-pass)

## The Critical Discovery

Before dispatching scouts, check if the target docs site offers a **single
concatenated file**. In this case, `/docs/llms-full.txt` was a 3.16 MB /
67,129-line markdown file containing **all 180 doc pages concatenated**.
This replaced 180 individual page-crawl calls with one `web_extract`.

**Always check these patterns first:**
- `/docs/llms-full.txt` — Hermes Agent and derivative doc sites
- `/llms.txt` — emerging convention for AI-friendly doc indexes
- `/docs/index.xml` — sitemap with all URLs
- "Download as Markdown" or "Download All" links

## Cluster Strategy

The 3MB source was split into **5 clusters by logical section**, not by size:

| Cluster | Section | Size | Pages | Scout produced |
|---------|---------|------|-------|----------------|
| A | Getting Started + User Guide | 414 KB | ~17 pages | CLI, TUI, profiles, security model |
| B | Features + Skills | 800 KB | ~42 pages | Skills system, curator, memory, tools, voice |
| C | Automation + Messaging | 500 KB | ~32 pages | Cron, delegation, kanban, Telegram/Discord/Slack |
| D | Integrations + Guides | 510 KB | ~40 pages | MCP, providers, credential pools, Python library |
| E | Developer Guide + Reference | 871 KB | ~49 pages | Agent loop, prompt assembly, context compression |

**Sizing heuristic:** 300-900 KB per chunk. Small enough for a subagent's
context window to process, large enough to contain coherent section context.
Never split mid-section.

## Dispatch Pattern

```yaml
tasks:
  - goal: "Read cluster-A.md and create wiki pages for all entities,
           concepts, and comparisons. Follow wiki conventions: frontmatter,
           tags, sourcelinks, provenance markers, ≥2 wikilinks per page."
    context: "Wiki at ~/wiki. SCHEMA at ~/wiki/SCHEMA.md. Domain=orchestration.
              Write content pages to ~/wiki/entities/, ~/wiki/concepts/.
              Save raw source to ~/wiki/raw/articles/ with frontmatter.
              Do NOT update index.md or log.md."
  - goal: "..."  # same for cluster B, C, D, E
```

**Critical context items passed to each scout:**
- Wiki path and SCHEMA rules
- Domain tag to use
- "Write wiki pages, not descriptions — filesystem IS the deliverable"
- "Antworte auf Deutsch" (since Basti prefers German)

## Concurrent Queen Work

While 5 scouts ran in parallel, the queen:
1. Checked **memory** for existing patterns relevant to the new docs
2. Created **cross-domain pages** in `_meta/cross-domain/` that bridge
   old wiki material (AI/ML models, MoE tuning) with new (Hermes architecture)
3. Pre-wrote **scaffolding pages** (`hermes-architecture-overview.md`,
   `hermes-agents-vs-tools-vs-skills.md`) that scouts would link to

This was critical because scouts from cluster B (Skills) would link to
"hermes-architecture-overview" which cluster E (Developer Guide) would
create — without the scaffold, that link breaks.

## Consolidation Phase

After all 5 scouts completed:

1. **Verify exists**: `find ~/wiki -type f -name "*.md" | wc -l` → 199
2. **Domain distribution**: `grep -r "^domain:" --include="*.md" | sort | uniq -c`
3. **Lint pass**: built a Python script that:
   - Extracts all `[[wikilinks]]`, excluding those inside code fences
   - Builds a resolvable index with 4 entries per page: filename stem,
     slugified stem, raw title, slugified title
   - Flags any wikilink that resolves to none of the 4
4. **Iterative stub cycle**: lint → find broken → resolve alias or create
   stub → re-lint → repeat until 0 broken (typically 4-6 cycles for 100+ pages,
   expect 50-150 rounds of fixes)

## Lessons Learned

### 1. Scout output quality varies by cluster

| Cluster | Pages produced | Wikilinks/page | Quality note |
|---------|:--------------:|:--------------:|-------------|
| A | 5 | 2.5 | Clean, focused |
| B | 12 | 3.2 | Best — used llm-wiki skill context |
| C | 8 | 3.0 | Good — followed structure closely |
| D | 7 | 2.8 | Average — some raw articles missing frontmatter |
| E | 15 | 3.5 | Most pages — some oversized |

**Fix for raw articles missing frontmatter:** Post-hoc scan for raw files
where first line is not `---`, add frontmatter with computed sha256.

### 2. Slug normalization dominates the post-merge work

Expect 50-150 broken links from slug mismatches per 100 pages ingested.
The two most common patterns:

| Wikilink written | Actual slug | Fix |
|-----------------|-------------|-----|
| `[[qwen-3.5-9b]]` | `qwen-3-5-9b-alibaba-qwen-team` | `[[qwen-3-5-9b-alibaba-qwen-team\|...]]` |
| `[[hermes-agent#Feature]]` | `hermes-agent` | `[[hermes-agent\|...]]` (strip anchor) |

**Iteration count:** 5-7 lint → fix cycles to go from 132 broken → 0.

### 3. 100% lint-pass on content pages IS achievable

- After the stub-resolution cycle: **0 broken out of 782 wikilinks**
- The remaining "broken" links are in SCHEMA.md and log.md (inline
  `[[wikilinks]]` used as syntax examples) — **deliberately excluded**
- **Target: 95%+ with no broken links in content pages**

### 4. Domain distribution exploded for orchestration

Pre-ingest: orchestration=6, ai-ml=25, personal=9
Post-ingest: orchestration=75, ai-ml=25, cross-domain=17, personal=12, meta=3

The Hermes docs are overwhelmingly orchestration material. This is expected
but worth flagging to the user — the wiki balance shifted dramatically.

## Concrete Timeline

| Phase | Wall time | Notes |
|-------|:---------:|-------|
| Recon + discovery | 3 min | Single `web_extract` on llms-full.txt |
| Split into 5 clusters | 2 min | Using `csplit` by section headers |
| Dispatch 5 scouts | 1 min | `delegate_task` with 5 tasks |
| While scouts work | 15 min | Queen: cross-domain pages, scaffolds, memory check |
| Scouts complete | — | All 5 reported independently |
| Lint cycle 1 | 5 min | 132 broken found |
| Stub round 1 | 8 min | 50+ stubs + alias fixes |
| Lint cycle 2 | 3 min | 64 broken remaining |
| Stub round 2 | 5 min | More stubs |
| Lint cycle 3 | 3 min | 16 broken |
| Final stubs + fixes | 4 min | 0 broken |
| Git commit | 1 min | `0c32665` on main |
| **Total** | **~50 min** | 70→131 pages, 782 wikilinks |

## Commands to Reproduce

```bash
# 1. Discover the concat file
web_extract "https://hermes-agent.nousresearch.com/docs/"

# 2. Download llms-full.txt
curl -sL "https://hermes-agent.nousresearch.com/docs/llms-full.txt" \
  > ~/wiki/raw/articles/hermes-agent-docs-llms-full-2026-07-17.md

# 3. Split into clusters (by ## headers, roughly even size)
csplit raw/articles/hermes-agent-docs-llms-full-2026-07-17.md \
  '/^## Getting/' '/^## Using Hermes/' '/^## Automation/' \
  '/^## Integrations/' '/^## Developer Guide/'

# 4. Verify scout output
find ~/wiki -type f -name "*.md" | wc -l

# 5. Domain distribution
grep -r "^domain:" ~/wiki/ --include="*.md" | grep -v "raw/" | sort | uniq -c

# 6. Count wikilinks
grep -roh "\[\[[^]]*\]\]" ~/wiki/ --include="*.md" | grep -v "raw/" | wc -l

# 7. Full lint (Python)
python3 -c "
import re, sys
from pathlib import Path
wiki = Path.home() / 'wiki'
slugs = set()
for p in wiki.rglob('*.md'):
    if 'raw/' in str(p.relative_to(wiki)): continue
    slugs.add(p.stem)
    text = p.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'^title:\s*(.+)$', text, re.M)
    if m: slugs.add(re.sub(r'[^\w]+', '-', m.group(1).strip().lower()).strip('-'))
broken = 0; total = 0
excluded = {'SCHEMA.md', 'log.md', 'index.md'}
for p in wiki.rglob('*.md'):
    if 'raw/' in str(p) or p.name in excluded: continue
    text = re.sub(r'\x60\x60\x60.*?\x60\x60\x60', '', 
                  p.read_text(encoding='utf-8', errors='ignore'), flags=re.S)
    for m in re.finditer(r'\[\[([^\]\|]+?)(\|[^\]]+)?\]\]', text):
        link = m.group(1).strip().split('#')[0]; total += 1
        if not link: continue
        if re.sub(r'[^\w]+', '-', link.lower()).strip('-') not in slugs: broken += 1
print(f'{broken} broken / {total} total')
"

# 8. Final git commit
git add -A
git commit -m "wiki: ingest HERMES-AGENT docs via 5-scout parallel
Source: llms-full.txt (3MB, 180 pages)
5 clusters: A-through-E, ~400-870KB each
Growth: 70→131 content pages, 199 files, 782 wikilinks
Domain: orchestration 6→75, ai-ml=25, cross-domain=17, personal=12"
```
