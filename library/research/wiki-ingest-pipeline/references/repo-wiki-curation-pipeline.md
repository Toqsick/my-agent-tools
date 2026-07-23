# Repo → Wiki Curation Pipeline

> **Proved:** 2026-07-22 on Toqsick/greyscripts — 65 pages, 8 subagents, ~30 min end-to-end.

End-to-end pattern for turning a GitHub repo into a structured wiki. The
wiki lives in a local `wiki/` folder inside the repo on a feature branch,
then opens as a PR. This is the only path an AI agent can drive without
Web-UI access (GitHub Wiki-Pages are not pushable via API — see Pitfalls).

## When to Use This Skill

Use this when the user says:

- "Create a wiki for <github-org>/<repo>"
- "Make a structured index.md / Home.md for this repo"
- "Document all tools / modules / pages in this codebase as a wiki"
- "Set up a docs/ wiki for this repo"

**Pre-condition:** the repo exists on GitHub. You will `git clone` it,
add a `wiki/` folder, commit + push to a feature branch, and open a PR.

**Not for:** Karpathy-style LLM wikis (frontmatter, raw/, log.md) — see
the main `wiki-ingest-pipeline` flow instead. This file is specifically
for **curating wikis from existing source code**.

## The 5-Wave Architecture

```
Wave 0: Setup (Queen only)
  ├─ git clone <repo> to /tmp/<repo>-local
  ├─ Checkout feature branch (or create from develop)
  ├─ Merge necessary refs (e.g. develop + main if they diverged)
  ├─ Write Home.md (INDEX), _Sidebar.md, _Footer.md
  └─ Commit + push (do NOT open PR yet)

Wave 1: Working-Subagents (5 parallel)
  ├─ Subagent A: Tools/<Domain>-X (one page per source file)
  ├─ Subagent B: Patterns/<Category> (one page per category)
  ├─ Subagent C: Docs/<Doc-Name> (one page per repo doc)
  ├─ Subagent D: Development/<Guide-Name>
  └─ Subagent E: Meta/<Page-Name> (Quickstart, Install, Changelog)

Wave 2: Tier-C Sub-Pages (1-2 subagents)
  ├─ Subagent F: Detail-Pages for complex items (API-Referenz, CheatSheets)

Wave 3: QA-Subagents (3 parallel)
  ├─ Subagent G: Linter (Em-Dashes ≤ 1, En-Dashes = 0, Boldface = 0, page-size)
  ├─ Subagent H: Completeness Auditor (vs repo inventory)
  └─ Subagent I (optional): Cross-link Validator

Wave 4: Queen-Verify + Integration
  ├─ Cross-link validator (2-pass with .md strip)
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

Total time: ~30 min for 50-100 pages.

## Briefing Template Per Wave

Each implementer subagent in Wave 1 receives the same briefing template
with these CRITICAL CONTEXT fields. **Do not skip — they are the
difference between a clean wave and 200 broken links afterward.**

```markdown
REPO-PFAD: <absolute path to /tmp/<repo>-local>
ZIEL-ORDNER: <repo>/wiki/

DEINE TOOLS (<N> <source-pattern>):
<numbered list with exact file paths>

OUTPUT-NAMING:
<exact mapping table, e.g.:
  - build_all → Tool-build-all.md
  - fix_perms → Tool-fix-perms.md
  - scp_upload → Tool-scp-upload.md
  - smtp_enum → Tool-smtp-enum.md
  - wifi_crack → Tool-wifi-crack.md>

PAGE-FORMAT pro <Page>:
<complete markdown skeleton with all required fields>

WICHTIG:
- Wiki-Pages nutzen KEIN Frontmatter (Plain-Markdown)
- Cross-Links als relative Pfade: [Tool-lib-core](Tool-lib-core)
- Externe Repo-Links mit voller URL
- Sprache: Deutsch
- Wiki-Stand: 2026-07-22 als Datum
- Em-Dashes (—) ≤ 1 pro Page, En-Dashes (–) = 0
- Mid-Sentence Boldface = 0
- KEIN .md-Suffix in Cross-Links (nur [Home](Home) nicht [Home](Home.md))
```

The naming-convention table is what prevents the 5-way Tool-* underscore
→ kebab-case mess. Ship it pre-baked.

## Queen-Verify 2-Pass Cross-Link Validator

The single most important Queen step after Wave 3. Run this exact script:

```python
import re
from pathlib import Path

WIKI = Path('/path/to/repo/wiki')
pages = {p.stem for p in WIKI.glob('*.md')}  # stems, no .md

broken = []
for p in WIKI.glob('*.md'):
    content = p.read_text()
    # Strip code-fences (docs link to code samples)
    content = re.sub(r'```.*?```', '', content, flags=re.S)
    for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
        target = m.group(2)
        if target.startswith('http') or target.startswith('#'):
            continue
        # TWO-DIRECTION .md strip
        t = target.split('#')[0]
        t_clean = t[:-3] if t.endswith('.md') else t
        if t_clean and t_clean not in pages:
            broken.append((p.name, target))

print(f'BROKEN: {len(broken)}')
for src, tgt in broken[:20]:
    print(f'  {src} -> {tgt}')
```

**Expected:** `BROKEN: 0`. If > 0, fix with sed sweeps BEFORE commit.

## Common sed Fixes After Queen-Verify

```bash
cd <repo>/wiki

# Fix Home ↔ Home.md mismatch (subagent created INDEX.md, want Home.md)
[ -f INDEX.md ] && [ ! -f Home.md ] && mv INDEX.md Home.md
sed -i 's|\[INDEX\](INDEX)|[Home](Home)|g; s|(INDEX)|(Home)|g' \
  Tools-Overview.md _Sidebar.md _Audit_*.md

# Fix Tool- naming (underscores → kebab-case)
sed -i \
  -e 's|Tool-build_all|Tool-build-all|g' \
  -e 's|Tool-fix_perms|Tool-fix-perms|g' \
  -e 's|Tool-scp_upload|Tool-scp-upload|g' \
  -e 's|Tool-smtp_enum|Tool-smtp-enum|g' \
  -e 's|Tool-wifi_crack|Tool-wifi-crack|g' \
  Tool-*.md _*.md
```

## Page-Count Targets

| Tier | Description | Page-Count |
|------|-------------|------------|
| A | Skeleton: Home + Sidebar + Footer + 6 hub pages | 10-15 |
| B | Full source coverage: 1 page per source file + categories | 40-80 |
| C | Detail + CheatSheets for complex items | 80-150 |

Greyscripts (Tier A+B+C): 65 pages in 30 min.

## Worked Example: Toqsick/greyscripts 2026-07-22

| Wave | Subagent | Goal | Duration | Output |
|------|----------|------|----------|--------|
| 0 | Queen | Setup, clone, branch, merge main+develop, write Home/Sidebar/Footer | 5 min | 3 pages |
| 1A | A | 33 Tool-Pages + Tools-Overview | 234s | 34 pages |
| 1B | B | 7 Pattern-Pages | 209s | 7 pages |
| 1C | C | 8 Doc-Pages (Arch/Roadmap/Bug-Patterns/etc.) | 168s | 8 pages |
| 1D | D | 3 Dev-Pages (Setup/Contribution/Security) | 67s | 3 pages |
| 1E | E | 3 Meta-Pages (Quickstart/Install/Changelog) | 120s | 3 pages |
| 2 | F | 5 Tier-C Detail-Pages | 450s | 5 pages |
| 3 | G | Linter: 31 Em-Dashes + 4 Boldface gefixt | 269s | _Audit_Lint.md |
| 3 | H | Completeness: 5 Coverage-Checks PASS | 112s | _Audit_Completeness.md |
| 4 | Queen | 2-Pass Cross-Link Validator + Naming sed + Home.md rename | 3 min | 0 broken links |
| 5 | Queen | wiki/README.md + Commit + gh pr create | 2 min | PR #77 |

**Total: 65 pages, 6129 insertions, PR #77 created.**

## Gotchas (Greyscripts 2026-07-22)

1. **develop vs main divergence**: `git log origin/develop` showed older commits than `origin/main`. `patterns/` was only on main. Fix: `git merge origin/main -X theirs` before starting.

2. **Wiki-Repo Push fails**: `git push -u origin wiki` → "Repository not found" because GitHub Wiki-Repo doesn't exist until first Web-UI page. **Pivot immediately** to `wiki/` folder in main repo.

3. **gh repo create <name>.wiki**: errors with "Name cannot end in .wiki". Don't try.

4. **Subagent creates INDEX.md not Home.md**: matches the user wording literally. Detect early via `ls Home.md INDEX.md`, fix in Queen-Verify Wave 4.

5. **Cross-link `[Home](Home.md)` vs `[Home](Home)`**: both legal Markdown. Validator must strip `.md` in BOTH directions.

6. **Tool-Naming underscores**: subagent forgets the mapping. Either pre-bake the mapping table in briefing OR run sed sweep in Queen-Verify.

7. **Audit-Files break Wiki convention**: `_Audit_Lint.md` and `_Audit_Completeness.md` contain Em-Dashes intentionally (they are reports). They are NOT Wiki-Pages, but the cross-link validator scans them too. This is fine — just count Em-Dashes only in non-`_Audit_*` files.

8. **Branch strategy**: Work on `feat/wiki-initial` branched from `develop`. Never push directly to main or develop for wiki work. Open PR as Draft.

## Mnemosyne Anchors (Recommended)

After completing a repo→wiki curation, persist these facts:

- `wiki_aufbau_<YYYY-MM-DD>` — main fact (Befüllt, Stats, Lessons)
- `wiki_subagent_pattern` — 5-Wellen-Orchestration-Muster
- `wiki_github_quirk` — Wiki-nicht-per-API-erstellbar
- `wiki_naming_kebab` — underscores → kebab-case Tool-Naming