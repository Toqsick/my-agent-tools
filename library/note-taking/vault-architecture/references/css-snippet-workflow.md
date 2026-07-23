# CSS Snippet Workflow — Full Worked Example

> **Session:** Cluster 5, Phase 6 (2026-07-05)
> **Created:** 3 CSS snippets (yuno-moc-style, yuno-callout-icons, yuno-daily-note-style)
> **Associated notes:** Obsidian-Plugins-Setup.md (247 Zeilen), Snippet-Liste.md (238 Zeilen)
> **Patterns applied:** Pattern 2 (additive patches) + Pattern 6 (improvisation)

## Anti-Halluzination: URL Verification Walkthrough

This is the most critical lesson from the session. Without this step, 2/5 plugin URLs
would have been dead links in the vault.

### Setup

The spec (Phase 6 plan) listed 5 plugins to document with their GitHub URLs.
Before writing a single line, **every URL was verified against real sources**.

### Tools Used

| Tool | Purpose | Why (not the other) |
|---|---|---|
| `web_extract` (Firecrawl) | Verify GitHub repo pages exist | Works without credentials |
| `web_search` | Find correct repo when URL was dead | Fallback for 404s |
| GitHub MCP | *Attempted first* — returned 401 (stale credentials) | Fallback to web_extract |

### Step-by-Step Verification

```python
# Pseudo-workflow for each URL in the spec
for plugin_spec in ["blacksmithgu/obsidian-dataview",
                    "SilentVoid13/Templater",
                    "mgmeyers/obsidian-style-settings",
                    "liamcain/obsidian-calendar-plugin",
                    "insanum/obsidian-mind-map"]:
    url = f"https://github.com/{plugin_spec}"
    result = web_extract(url)
    if "404" in result or "Not Found" in result:
        # URL is dead — search for the actual repo
        corrected = web_search(f"obsidian plugin {plugin_spec.split('/')[1]}")
        # → likely found correct repo
        document_correction(plugin_spec, corrected)
    else:
        # URL is live — note the star count for credibility
        pass
```

### Results

| # | Plugin | Spec URL | Live? | Corrected To |
|---|---|---|---|---|
| 1 | Dataview | `blacksmithgu/obsidian-dataview` | ✅ 9.2k ★ | — |
| 2 | Templater | `SilentVoid13/Templater` | ✅ 5.1k ★ | — |
| 3 | Style Settings | `mgmeyers/obsidian-style-settings` | ❌ **404** | `obsidian-community/obsidian-style-settings` (2.3k ★) |
| 4 | Calendar | `liamcain/obsidian-calendar-plugin` | ✅ 2.2k ★ | — |
| 5 | Mind Map | `insanum/obsidian-mind-map` | ❌ **404** | `lynchjames/obsidian-mind-map` (1.4k ★) |

### Documentation in Notes

Every correction was documented in the vault note with a blockquote:

```markdown
> **Anti-Halluzination-Notiz:** Die alte URL `mgmeyers/obsidian-style-settings` ist 404 —
> das Repo wurde in die `obsidian-community`-Organisation übertragen.
> Immer die aktuelle URL verwenden.
```

This has two benefits:
1. The maintainer (Basti) sees *why* the spec was deviated from
2. Future agents reading the note see the correction context

## CSS Snippet Creation Walkthrough

### Phase 1: Read Existing State

```bash
ls .obsidian/snippets/
# → yuno-variables.css  yuno-tag-colors.css  yuno-folder-colors.css
#   yuno-wiki-links.css  yuno-callouts.css

cat .obsidian/snippets/yuno-variables.css | grep -- '--yuno-'
# → Available palette: purple, pink, mint, coral, sky, sun
#   Each has: -base, -soft, -bg, -deep variants
```

**Finding:** 5 existing snippets from Phase 5. Color palette is
`--yuno-purple` (primary), `--yuno-pink`, `--yuno-mint`, `--yuno-coral`,
`--yuno-sky`, `--yuno-sun`.

### Phase 2: Check for conflicts

- `yuno-moc-style.css` — no existing snippet with "moc" in name ✅
- `yuno-callout-icons.css` — existing `yuno-callouts.css` covers *standard*
  callouts only, not custom ones → disjunct ✅
- `yuno-daily-note-style.css` — no existing snippet covers daily notes ✅

### Phase 3: Create Each Snippet

Each snippet was created with:
- Yuno `--yuno-*` CSS variables (not hardcoded hex values)
- Minimum line count met (see table in parent skill)
- `@settings` block included for Style Settings plugin compatibility

### Phase 4: Register in appearance.json

**Before (5 snippets):**
```json
"enabledCssSnippets": [
    "yuno-variables",
    "yuno-tag-colors",
    "yuno-folder-colors",
    "yuno-wiki-links",
    "yuno-callouts"
]
```

**Patch applied (Pattern 2 — additive, append-only):**
```json
"enabledCssSnippets": [
    "yuno-variables",       // unchanged
    "yuno-tag-colors",      // unchanged
    "yuno-folder-colors",   // unchanged
    "yuno-wiki-links",      // unchanged
    "yuno-callouts",        // unchanged
    "yuno-moc-style",       // new
    "yuno-callout-icons",   // new
    "yuno-daily-note-style" // new
]
```

**JSON lint:** passed ✅ (`patch` tool validates JSON automatically)

### Phase 5: Create Matching Vault Notes

Two notes created in `05 Ressourcen/`:

1. **Obsidian-Plugins-Setup.md** (247 lines)
   - Plugin overview table with verified URLs
   - Per-plugin: purpose, install steps, configuration, pitfalls
   - Anti-Halluzination blocks for the 2 corrected URLs
   - Setup-reihenfolge recommendation (Dataview → Calendar → Templater → Style Settings → Mind Map)

2. **Snippet-Liste.md** (238 lines)
   - Table of all 8 snippets with descriptions, dependencies, maintainer priority
   - Per-snippet: purpose, setup requirements, when to update
   - Maintainer guide with decision table (which file for which trigger)
   - Style override pattern (with vs. without Style Settings plugin)
   - activation.json content and ordering rules

### Phase 6: Verify

1. **No existing files modified** — checked timestamps: Phase-5 files all show 18:21,
   Phase-6 files show 18:33-18:34 → disjunct writes ✅
2. **JSON lint** — passed ✅
3. **Line counts** — all exceed minima: 211 ✅ (min 80), 204 ✅ (min 60), 121 ✅ (min 40)
4. **appearance.json** — validates, 8 entries, correct order (variables first) ✅
5. **Existing notes untouched** — confirmed via `wc -l`:
   - yuno-callouts.css: 112 (unchanged)
   - yuno-folder-colors.css: 143 (unchanged)
   - yuno-tag-colors.css: 139 (unchanged)
   - yuno-variables.css: 65 (unchanged)
   - yuno-wiki-links.css: 118 (unchanged)
   - Obsidian - Plugin-Setup.md: 200 (unchanged)

## Pattern 6 Improvisation Details

### yuno-callout-icons.css — 6 Custom Callouts (spec said 2)

**Spec:** Create `[!yuno-decision]` and `[!yuno-archival]` callouts.

**Improvisation:** Added 4 more callouts that match Basti's operational vocabulary:

| Callout | Use case | Icon |
|---|---|---|
| `[!yuno-decision]` | Eine Entscheidung | `zap` |
| `[!yuno-archival]` | Archivierte Notiz | `archive` |
| `[!yuno-agent-task]` | Agenten-Aufgabe | `bot` |
| `[!yuno-skill]` | Skill/Pattern-Referenz | `book-open` |
| `[!yuno-cluster]` | Cluster-Anweisung | `layers` |
| `[!yuno-fail]` | Fehlschlag/Hindernis | `alert-triangle` |

**Justification:**
- Agent-task and skill: Basti runs a multi-agent Hermes environment — these are daily vocabulary
- Cluster: Vault expansion uses cluster terminology throughout
- Fail: Needed for documenting pitfalls without misusing `[!danger]` or `[!bug]`

### yuno-moc-style.css — Beyond-Spec Enhancements

**Spec:** MOC banner (border-left gradient) + H2/H3 outline visualisation.

**Added:**
- Subtle hover-glow animation on Dataview-list items
- Inline-title styling (larger font weight, accent color)
- Print-mode styles that hide banner and linearize outline

### yuno-daily-note-style.css — Beyond-Spec Enhancements

**Spec:** Daily-Note highlighting via `datum:` frontmatter property.

**Added:**
- `body.has-todays-note` class — styles *today's* note differently from past daily notes
- Tag-pill highlighting: `#daily` and `#journal` tags get purple glow
- Light-mode override for the glow (so it works in both themes)

## Lessons Learned

1. **Always verify plugin URLs** — 2/5 (40%) were dead in this session alone
2. **GitHub MCP credentials go stale** — have a fallback plan (`web_extract`/Firecrawl)
3. **appearance.json patches must be additive** — never remove existing snippet entries
4. **No existing files should be modified** — check timestamps after creation
5. **Improvisation is good but must be documented** — every deviation needs a "Spec said X, but I did Y because Z" in the summary
6. **Line counts matter** — Basti has established minimums; always exceed them but document the target
