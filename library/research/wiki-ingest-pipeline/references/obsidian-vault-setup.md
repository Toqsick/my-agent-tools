# Obsidian Vault Setup for LLM Wiki

> Complete `.obsidian/` configuration and MOC creation pattern for turning
> a Karpathy-style LLM wiki into an Obsidian vault. Derived from the
> Basti Wiki v0.5.0 setup (173 content pages, 5 domains, 1239 wikilinks).

## When This Reference Applies

Use this when:
- Setting up a fresh wiki directory as an Obsidian vault for the first time
- The wiki has 50+ content pages and needs domain-organized navigation
- Users will browse the wiki via Obsidian's Graph View, Dataview, or Quick Switcher
- Multiple agents write to the same wiki and need vault-level conventions

## Architecture

```
wiki/
├── .obsidian/                    ← Git-tracked vault config
│   ├── app.json                  ← editor behavior
│   ├── appearance.json           ← theme, fonts, layout
│   ├── core-plugins.json         ← enabled built-in plugins
│   └── community-plugins.json    ← enabled community plugins
├── .gitignore                    ← excludes per-user workspace state
├── README.md                     ← vault-level readme
├── _meta/
│   ├── moc-wiki-root.md          ← top-level navigation MOC
│   ├── moc-orchestration.md      ← orchestration domain (101 pages)
│   ├── moc-ai-ml.md             ← ai-ml domain (32 pages)
│   ├── moc-personal.md          ← personal domain (13 pages)
│   ├── moc-cross-domain.md      ← cross-domain (24 pages)
│   └── ... (domain-specific MOCs)
├── entities/                     ← entities (models, people, orgs)
├── concepts/                     ← concepts, techniques, patterns
├── comparisons/                  ← side-by-side analyses
├── queries/                      ← filed query results
├── lessions/                     ← lessons learned
└── raw/                          ← immutable sources (not indexed by Obsidian)
```

## .obsidian/ Config Files

### app.json

```json
{
  "alwaysUpdateLinks": true,
  "attachmentFolderPath": "raw/assets",
  "newFileLocation": "current",
  "newLinkFormat": "shortest",
  "showUnsupportedFiles": false,
  "useMarkdownLinks": false,
  "showLineNumber": false,
  "spellcheck": false,
  "tabSize": 2,
  "readableLineLength": true,
  "strictLineBreaks": false,
  "promptDelete": false
}
```

Key settings:
- `alwaysUpdateLinks: true` — when a file is renamed, Obsidian auto-updates all `[[wikilinks]]` to it. Essential for multi-agent wikis where agents may rename files.
- `newLinkFormat: "shortest"` — creates `[[slug]]` not `[[dir/slug]]`. Keeps links portable across directory restructures.
- `attachmentFolderPath: "raw/assets"` — screenshots, images go to the existing raw/ directory structure.

### appearance.json

```json
{
  "accentColor": "#8b5cf6",
  "baseFontSize": 15,
  "cssTheme": "Minimal",
  "enabledCssSnippets": [],
  "interfaceFontFamily": "Inter",
  "monospaceFontFamily": "JetBrains Mono",
  "nativeMenus": false,
  "showViewHeader": true,
  "theme": "obsidian",
  "translucency": false
}
```

The accent color (`#8b5cf6` = purple) differentiates wiki vaults from other vaults in the Obsidian switcher. The Minimal theme works well for large markdown knowledge bases.

### core-plugins.json

Enable these 16 core plugins for full wiki navigation:

```json
{
  "audio-recorder": false,
  "backlink": true,
  "bookmarks": true,
  "command-palette": true,
  "daily-notes": false,
  "file-explorer": true,
  "file-recovery": true,
  "global-search": true,
  "graph": true,
  "markdown-importer": false,
  "note-composer": true,
  "outgoing-link": true,
  "outline": true,
  "page-preview": true,
  "properties": true,
  "publish": false,
  "random-note": false,
  "slash-command": false,
  "slides": false,
  "starred": false,
  "switcher": true,
  "sync": false,
  "tag-pane": true,
  "templates": false,
  "word-count": false,
  "workspaces": true,
  "zk-prefixer": false
}
```

Critical plugins for wiki navigation:
- **backlink** — shows which pages link TO the current one
- **outgoing-link** — shows which pages the current one links TO
- **graph** — visualizes the entire knowledge network (Ctrl/Cmd+G)
- **tag-pane** — browse by tags from SCHEMA taxonomy
- **switcher** — Ctrl/Cmd+O for quick file search
- **properties** — displays YAML frontmatter as a structured panel
- **bookmarks** — save frequently-referenced pages
- **workspaces** — save different view layouts (editing vs. browsing)

### community-plugins.json

When community plugins are enabled, register these:

```json
{
  "enabled": true,
  "list": [
    {
      "id": "dataview",
      "name": "Dataview",
      "version": "0.5.67",
      "author": "Michael Brenan",
      "description": "Query YAML frontmatter as database. Essential for tag-based page listings, stats, and cross-references.",
      "repo": "blacksmithgu/obsidian-dataview"
    },
    {
      "id": "templater",
      "name": "Templater",
      "version": "2.9.1",
      "author": "SilentVoid13",
      "description": "Template engine for new pages. Useful for standardizing frontmatter across agent-created pages.",
      "repo": "SilentVoid13/Templater"
    },
    {
      "id": "obsidian-excalidraw-plugin",
      "name": "Excalidraw",
      "version": "2.5.0",
      "author": "Zsolt Viczian",
      "description": "Hand-drawn diagrams in markdown. Useful for architecture comparisons that defies pure text.",
      "repo": "zsviczian/obsidian-excalidraw-plugin"
    },
    {
      "id": "obsidian-git",
      "name": "Obsidian Git",
      "version": "2.31.1",
      "author": "Denis Olehov",
      "description": "Auto-commit and push from Obsidian. Keeps the wiki synced across machines and agents.",
      "repo": "denolehov/obsidian-git"
    }
  ]
}
```

Dataview is the most important — it turns the wiki into a queryable database. Example queries:

```dataview
TABLE tags, created, confidence
FROM "entities"
WHERE contains(tags, "model")
SORT created DESC

TABLE rows.file.link AS "Page", rows.tags AS "Tags"
FROM "concepts"
GROUP BY domain
```

## MOC Creation Pattern

MOCs (Maps of Content) serve as domain-organized navigation. Create one per domain when the wiki exceeds 50 pages.

### MOC Structure

```markdown
# 🐝 Orchestration — Map of Content

> Domain overview: 101 pages covering multi-agent orchestration patterns,
> Hermes-V7 architecture, cron-jobs, webhooks, and agent dispatch workflows.
> Last updated: 2026-07-17

## 🏛️ Core Patterns

- [[queen-bee-pattern]] — Queen-Bee + Scout-Schwarm Orchestrierung
- [[multi-agent-orchestration-patterns]] — Allgemeine Multi-Agent Patterns
- [[agent-dispatch-comparison]] — Vergleich: delegate_task vs. cron vs. background terminal
- [[fable-orchestration-pattern]] — Fable-pattern für strukturierte Workflows

## 🔧 Hermes-V7 Infrastructure

- [[hermes-v7-architecture]] — Hermes V7 Gesamtarchitektur
- [[hermes-gateway-setup]] — Gateway für Telegram/Discord/SMS
- [[cron-job-management]] — Scheduled Tasks in Hermes

## 🔗 Cross-Domain

See also: [[moc-ai-ml|🧠 AI/ML MOC]], [[moc-personal|🌱 Personal MOC]]
```

### When to Create MOCs

| Wiki Size | MOCs Needed | Pattern |
|---|---|---|
| < 50 pages | 0 | index.md + graph view suffice |
| 50-150 pages | Per-domain | One MOC per domain in `_meta/moc-<domain>.md` |
| 150+ pages | Hierarchical | Per-domain MOCs + sub-domain MOCs for domains with 40+ pages |

### MOC Naming Convention

- `_meta/moc-wiki-root.md` — top-level MOC linking to all domain MOCs and key meta-pages. This is the first page a user sees when opening the vault.
- `_meta/moc-<domain>.md` — per-domain MOC. Example: `moc-orchestration.md`, `moc-ai-ml.md`, `moc-personal.md`.
- `_meta/cross-domain/` — cross-domain synthesis pages (not MOCs per se, but companion content)

The root MOC contains:
1. Domain links (each → its MOC)
2. Key meta-pages (SCHEMA, log, index)
3. Quick-links to the most recently updated pages (top 10)
4. Stats: total pages per domain, last update date

### Domain MOC Content

Each domain MOC includes:
1. Domain header with page count and last-updated date
2. Sectioned lists of pages (grouped by sub-topic, not flat)
3. Cross-links to other domain MOCs
4. Dataview queries embeddable if community plugins are enabled

## .gitignore for Vault Directories

```gitignore
# Per-user Obsidian workspace state (not portable between machines)
.obsidian/workspace.json
.obsidian/workspace.json.bak
.obsidian/workspace-mobile.json
.obsidian/cache/
.obsidian/plugins/
.obsyman/
.trash/

# OS files
.DS_Store
Thumbs.db

# Raw extraction artifacts
raw/assets/*.excalidraw
raw/assets/*.svg.tmp
```

The `.obsidian/workspace.json` exclusion is critical — workspace state (open tabs, pane layout) is machine-specific and causes merge conflicts when multiple agents commit to the same repo. The `.obsidian/plugins/` directory is omitted because community plugins auto-restore from community-plugins.json on first open.

## First-Time Vault Setup

```bash
# 1. Create .obsidian directory and write config files
mkdir -p ~/wiki/.obsidian
# write app.json, appearance.json, core-plugins.json, community-plugins.json

# 2. Create MOC structure
mkdir -p ~/wiki/_meta
# write moc-wiki-root.md + per-domain MOCs

# 3. Write vault README
# ~/wiki/README.md explains what the wiki covers

# 4. Update .gitignore with obsidian exclusions

# 5. Verify via Obsidian
obsidian ~/wiki

# 6. First open: accept "Enable Community Plugins" prompt
# If the prompt doesn't appear:
#   Settings → Community Plugins → Turn on → Install Dataview + Obsidian Git

# 7. Git-track the vault config
git add .obsidian/ _meta/ README.md .gitignore
git commit -m "vault: initialize Obsidian config with MOC navigation"
```

## Relationship to index.md

The `index.md` and MOC pages serve different purposes:

| File | Purpose | Audience | Auto-maintained? |
|---|---|---|---|
| `index.md` | Agent-readable content catalog (one-line summaries per page) | Agent | Yes (by ingest pipeline) |
| `moc-*.md` | Human-readable navigation (sectioned with descriptions) | Human | Semi (agent creates, human refines) |
| SCHEMA.md | Agent rules and conventions | Agent | Yes (agent extends) |

The index.md is long and mechanical — optimized for search_files and grep.
MOCs are short and curated — optimized for human browsing in Obsidian's file explorer.

## Migrating an Existing Wiki to Obsidian

If the wiki already exists without `.obsidian/` config:

```bash
mkdir -p ~/wiki/.obsidian
# Write the 4 config files (app.json, appearance.json, core-plugins.json, community-plugins.json)
mkdir -p ~/wiki/_meta
# Write root MOC (scans existing pages and groups by directory)
# Optionally: per-domain MOCs (one per directory)
```

Update `.gitignore` to exclude workspace state, then:
```bash
git add .obsidian/ _meta/ README.md .gitignore
git commit -m "vault: add Obsidian integration to existing wiki"
```
