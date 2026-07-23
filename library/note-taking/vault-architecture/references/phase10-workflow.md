# Phase 10: Vault Infrastructure Execution

After visual theming (Phase 5/5.5), plugin expansion (Phase 8), and cross-link depth (Phase 3/7), **Phase 10 targets vault infrastructure reliability**: backup discipline, plugin management, graph.json tuning, Yuno-Dashboard creation, MOC-Home maintenance, and comprehensive verification.

## Trigger Conditions

- "CSS snippets erstellen" / "Theme-Snippets bauen"
- "Plugin-Setup-Guides schreiben" (with GitHub URLs to verify)
- "Snippet-Liste pflegen" / "appearance.json patchen"
- "Visuelle Theme-Expansion" / "Phase 5" / "Phase 6"
- "MOC-Styling" / "Callout-Icons" / "Daily-Note-Highlighting"
- "Graph-View hat alle Knoten in einer Farbe" (graph.json colorGroups-config)
- "Die Kreise machen den File-Explorer unübersichtlich" (Sanctum Theme)
- "Theme passt nicht" mit visueller Beschreibung (CSS-Override-Diagnose)

## Anti-Halluzination: Plugin URL Verification (Critical)

**Hard rule:** When creating plugin-setup notes that reference GitHub URLs, ALWAYS verify the URLs against real sources before writing. Never trust spec URLs blindly.

**Workflow:**

1. Extract all plugin GitHub URLs from the spec
2. Verify each via `web_extract` (Firecrawl) — works without GitHub credentials
3. If GitHub MCP returns 401 (stale credentials), fall back to `web_extract`
4. Cross-check: if a URL returns 404, find the actual repo via `web_search`
5. Document corrections in the note itself using `> **Anti-Halluzination-Notiz:**` blocks

**Proven example (2026-07-05 Cluster 5 — 5 Obsidian plugin URLs verified):**

| Plugin | Spec URL | Result | Action |
|---|---|---|---|
| Dataview | `blacksmithgu/obsidian-dataview` | ✅ 9.2k ★, live | Keep as-is |
| Templater | `SilentVoid13/Templater` | ✅ 5.1k ★, live | Keep as-is |
| Style Settings | `mgmeyers/obsidian-style-settings` | ❌ **404** — repo moved to org | Replace with `obsidian-community/obsidian-style-settings` (2.3k ★) |
| Calendar | `liamcain/obsidian-calendar-plugin` | ✅ 2.2k ★, live | Keep as-is |
| Mind Map | `insanum/obsidian-mind-map` | ❌ **404** — repo deleted/renamed | Replace with `lynchjames/obsidian-mind-map` (1.4k ★, Markmap engine) |

## CSS Snippet Creation Checklist

| Step | Action | Verification |
|---|---|---|
| 1 | Read existing snippets (avoid name/topic conflicts) | `ls <vault>/.obsidian/snippets/` |
| 2 | Check color palette from `yuno-variables.css` | Available `--yuno-*` variables |
| 3 | Create `.css` file referencing `var(--yuno-*)` | `wc -l` meets minimum |
| 4 | Add `@settings` block if Style Settings plugin is available | — |
| 5 | Register in `appearance.json` via additive patch | Append, never remove existing |
| 6 | Create matching vault note entry (Snippet-Liste.md, Plugin-Setup) | — |
| 7 | Verify no existing snippets modified | Compare timestamps or line counts |

## Minimum Line Counts (Basti's convention)

| Snippet Type | Minimum | Typical (actual) |
|---|---|---|
| Foundation variables (`yuno-variables`) | 50 | 65 |
| Tag colors (`yuno-tag-colors`) | 80 | 139 |
| Folder colors (`yuno-folder-colors`) | 80 | 143 |
| Wiki links (`yuno-wiki-links`) | 60 | 118 |
| Standard callouts (`yuno-callouts`) | 60 | 112 |
| **MOC style** (`yuno-moc-style`) | **80** | **211** |
| **Custom callout icons** (`yuno-callout-icons`) | **60** | **204** |
| **Daily note style** (`yuno-daily-note-style`) | **40** | **121** |

## Additive Patch Pattern for `appearance.json`

When adding new snippets, use Pattern 2 — never remove or reorder existing entries:

```json
// BEFORE: 5 snippets (Phase 5 baseline)
"enabledCssSnippets": [
    "yuno-variables",
    "yuno-tag-colors",
    "yuno-folder-colors",
    "yuno-wiki-links",
    "yuno-callouts"
]

// AFTER: 8 snippets (Phase 6) — existing 5 unchanged, 3 appended
"enabledCssSnippets": [
    "yuno-variables",
    "yuno-tag-colors",
    "yuno-folder-colors",
    "yuno-wiki-links",
    "yuno-callouts",
    "yuno-moc-style",          // new
    "yuno-callout-icons",      // new
    "yuno-daily-note-style"    // new
]
```

## Phase 5 Workflow (Proven 2026-07-05)

1. **Read existing snippets** — list directory, check for naming/topic conflicts
2. **Check `yuno-variables.css`** — know which `--yuno-*` colors are available
3. **Verify plugin URLs** — anti-halluzination check against real GitHub repos (see table above)
4. **Create CSS snippets** — one per file, Yuno color variables, meet minimum line count
5. **Create matching vault notes**
   - `05 Ressourcen/Obsidian-Plugins-Setup.md` — plugin overview with verified URLs, install steps, pitfalls
   - `05 Ressourcen/Snippet-Liste.md` — all active snippets with descriptions, maintainer guide
6. **Patch `appearance.json`** — additive, append-only
7. **Verify** — no existing files modified (timestamp check), JSON lint passes, line counts meet minima

## Snippet Naming Convention

```
yuno-<purpose>.css
```

All lowercase, hyphen-separated. Single purpose per file. Registered as `yuno-<purpose>` (without `.css` extension) in `enabledCssSnippets`.