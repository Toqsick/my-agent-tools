# Phase 5.5: Graph-View + Sanctum CSS Override

After visual theming (Phase 5), the vault's **knowledge graph** and **file explorer** often need additional config because Obsidian defaults show all graph nodes in one color, and theme-specific features (e.g. Sanctum's round letter-badges) can clutter the file explorer.

## Fix 1: Graph.json Tag-Colorization

**Problem:** The knowledge graph shows ALL nodes in the same color (white/gray) because `graph.json` has `"colorGroups": []` and `"showTags": false`.

**Fix:** Write `graph.json` with:
- `"showTags": true`
- `"colorGroups"` array with tag→color mappings using RGB-integer encoding (Obsidian's format):
```json
{"query": "tag:#moc", "color": {"a": 0.65, "rgb": 4286878434}},
{"query": "tag:#daily", "color": {"a": 0.65, "rgb": 2899180543}},
```

The RGB integer is the encoded CSS color as a signed int32. To convert a known CSS hex color to this format:
```python
def css_color_to_rgb_int(hex_color):
    """Convert '#a78bfa' → 4286878434 or similar Obsidian graph.json encoding."""
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    return (255 << 24) | (r << 16) | (g << 8) | b
```

**Proven 16-color mapping from 2026-07-05 (Basti's vault):**

| Tag | Cluster | RGB Int |
|-----|---------|---------|
| `#daily` | Coral-Orange | 2899180543 |
| `#moc` | Purple | 4286878434 |
| `#wiki` | Pink | 4281137716 |
| `#glossar` | Sun-Yellow | 4294953215 |
| `#kontext` | Blue-Sky | 4285396290 |
| `#projekt` | Sky-Blue | 4284788309 |
| `#ressource` | Purple | 4286878434 |
| `#bereich` | Mint | 4280420456 |
| `#skill` | Pink | 4281137716 |
| `#hermes` | Mint | 4280420456 |
| `#ai/#ki` | Sky-Blue | 4284788309 |
| `#vault` | Purple | 4286878434 |
| `#archiv` | Gray | 2873096319 |
| `#todo/#offen` | Coral-Orange | 2899180543 |

Also reduce `lineSizeMultiplier` to **0.45** (thinner edges, declutters graph) and `nodeSizeMultiplier` to **0.6** (smaller nodes, more overview).

## Color-Consolidation Heuristic

When auditing a vault's `graph.json`, always check for **RGB collisions** — multiple tag colorGroups sharing the same encoded RGB integer. This collapses 16 colorGroups to ~8-9 visually distinct colors.

```python
def find_rgb_collisions(color_groups):
    """Find tags sharing the same RGB value for potential consolidation."""
    by_rgb = {}
    for g in color_groups:
        rgb = g['color']['rgb']
        name = g['query'].replace('tag:#', '')
        by_rgb.setdefault(rgb, []).append(name)
    for rgb, tags in sorted(by_rgb.items(), key=lambda x: -len(x[1])):
        if len(tags) > 1:
            print(f"  {rgb} → {', '.join(tags)} ({len(tags)} tags)")
    return by_rgb
```

## Fix 2: Sanctum-Theme CSS Override (File-Explorer + Folder-Headers)

**Problem:** Sanctum theme injects colored circle-badges with letters next to each file name (e.g. "P" for Projekt, "R" for Ressource, "D" for Daily). This makes the file explorer visually noisy.

**Sanctum's DOM classes (verified 2026-07-05):**
- Top-level folders (01-08): `.nav-folder.mod-root > .nav-folder-title`
- Sub-folders: `.nav-folder:not(.mod-root) .nav-folder-title`
- File nodes: `.nav-file-title`
- Active file: `.nav-file-title.is-active`
- Title content: `.nav-file-title-content`, `.nav-folder-title-content`
- SVG icons: `svg.lucide-*` (Sanctum wraps file-type icons in these)
- Disable mechanism: `body.no-sanctum-icons` (alters SVG icon display)

**Folder-Colorization with Sanctum:** Use `:has(> .nav-folder-title[data-path="<folder-name>"])` on the `nav-folder.mod-root` level to target specific top-level folders.

**File-Explorer Cleanup Workflow:**
1. Create a new CSS snippet (e.g. `yuno-clean-file-explorer.css`) that:
   - Reduces opacity of `svg.lucide-*` icons to 0.45
   - Sizes icons down to 14px
   - Adds a `·` bullet before file names via `::before`
   - Adds `▸`/`▾` folder toggle indicators
   - Makes active file use the Yuno-Purple color scheme
2. Register the snippet in `appearance.json` (additive, never remove existing)
3. Update `Snippet-Liste.md` vault note with the new entry
4. Update `yuno-folder-colors.css` if needed to use correct Sanctum selectors
5. Verify: Obsidian restart (snippets aren't hot-reloaded), then check file explorer is clean

**Sanctum-Specific Selectors for Folder-Colors (Proven pattern):**
```css
.nav-folder.mod-root:has(> .nav-folder-title[data-path="01 Kontext"]) > .nav-folder-title {
  border-left: 4px solid var(--yuno-purple-deep) !important;
  background: linear-gradient(90deg, var(--yuno-purple-soft) 0%, transparent 75%) !important;
}
```

⚠️ **Known limitation (2026-07-05):** Obsidian's CSS engine may not support `:has-text()` pseudo-selector. Always use `:has(> .nav-folder-title[data-path="..."])` instead for Jest/Electron compatibility.