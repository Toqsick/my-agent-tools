# Phase 10 Infrastructure Execution (2026-07-05)

## Overview

Phase 10 targeted vault infrastructure reliability: plugin management, graph.json tuning, Canvases, Yuno-Dashboard creation, MOC-Home maintenance, and comprehensive verification.

## Key Learnings

### Plugin Download Pattern
- ALWAYS download `main.js`, `manifest.json`, `styles.css` individually from `releases/latest/download/<file>`
- NEVER download ZIP archives — returns 9-byte `{"error":"Not Found"}`
- Verify `minAppVersion` via `jq .minAppVersion manifest.json` vs `flatpak info md.obsidian.Obsidian | grep Version`

### community-plugins.json
- Must be a flat JSON array: `["plugin1", "plugin2"]`
- NOT `{"plugins": ["plugin1", "plugin2"]}` (silent loading failure)

### Atomic JSON Writes
- Use `jq '.field = "value"' file.json > file.json.tmp && mv file.json.tmp file.json`
- Direct `>` truncates file on jq error

### graph.json Folder Queries
- Use `path:"01 Kontext"` (quoted) for folders with spaces
- `folder:01 Kontext` fails silently without quotes

### Canvases
- Store at `08 Anhaenge/Excalidraw/<topic>.canvas`
- Node IDs must be 16 hex chars: `a1b2c3d400010001`
- Edge IDs similarly 16+ hex chars
- `type:"file"` paths are vault-relative (no `./` or `/`)

### Yuno-Dashboard
- 99+ lines with frontmatter `tags: [..., moc]` (moc is critical for Dataview queries)
- Must serve 5+ backlinks (Cron-Infrastruktur, Projekte-Repo-Map, MOC-KI, TokenTelemetry, MOC-Home)
- Create `CHANGELOG.md` with Phase table + Bug-Fixes + Lessons sections

### Skills as Vault Files
- Store reusable patterns at `05 Ressourcen/Skills/<topic>.md`
- Materialized skills from Phase 10: `obsidian-vault-color-consolidation.md`, `obsidian-canvas-factory.md`, `inline-gate-fallback.md`

## Critical Pitfalls Documented

| Pitfall | Impact | Mitigation |
|---|---|---|
| Plugin ZIP download | 9-byte error file | Download individual release files |
| minAppVersion > local | Broken plugin + config | Delete files, revert config |
| community-plugins.json object | Silent loading failure | Write flat array only |
| graph.json folder: without quotes | ColorGroups invisible | Use `path:"01 Kontext"` |
| jq > file.json directly | Truncation on error | Use tmp+mv pattern |
| MOC-Home patch duplicates headers | Double `## Übersicht` | grep -c after every patch |
| Obsidian running during .json edits | Config overwritten on close | Kill Obsidian first |
| Advisor voices hallucinate state | Duplicate work, wild goose chases | Ground-truth-check via terminal |

## Verification Command (Single Call)

```bash
find . -name "*.md" -not -path "*/.trash/*" -not -path "*/.obsidian/*" | wc -l
ls 08\ Anhaenge/Excalidraw/*.canvas 2>&1 | wc -l
ls .obsidian/plugins/
ls ~/.cache/vault-backups/phase10-*.tar.gz 2>/dev/null | wc -l
for f in .obsidian/*.json; do jq empty "$f" 2>/dev/null && echo "✓ $f"; done
jq '.enabledCssSnippets | length' .obsidian/appearance.json
ls .obsidian/snippets/ | wc -l
find . -maxdepth 1 -name '*.md' -size 0 2>&1 || echo "✓ no stubs"
grep -c "^## Übersicht" "MOC - Home.md"
grep "moc" Yuno-Dashboard.md | head -3
grep -c "Yuno-Dashboard" --include="*.md" -r . 2>/dev/null | grep -v ":0"
```

## Phase 10 Results (Verified)

- 124 notes, 4 canvases, 3 plugin dirs
- 4 sequential backups, 6/6 JSONs valid
- 14 CSS snippets enabled, 0 stubs in root
- MOC-Home: 1× `## Übersicht` (clean)
- Yuno-Dashboard: moc tag present, 14 backlink sources
