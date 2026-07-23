---

name: obsidian-visual-iteration-loop
description: |
  Use when you iterate Obsidian theme visuals via screenshot feedback — adjust colors, spacing, fonts, snippets — and want a loop that captures → diffs against spec → proposes the next edit.
  NOT for one-shot theme authoring, non-Obsidian note apps, or content edits inside notes (use obsidian-vault-quality-audit etc.).
  Closed-loop visual-iteration cycle for Obsidian themes: capture, compare to spec, propose next CSS/snippet edit, repeat until convergence.
version: 0.1.0
author: Hermes
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - Obsidian
    - theme
    - css
    - iteration
    - visual
    - feedback
license: MIT
trigger_keywords: ['obsidian', 'theme', 'loop', 'spec', 'next']
keywords: ['obsidian', 'theme', 'loop', 'spec', 'next']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['obsidian-vault-color-consolidation', 'obsidian-subagent-briefing-template', 'hermes-themes']
---

# Obsidian Visual Iteration Loop

A reusable workflow for tightening Obsidian theme customization through explicit user feedback. It does NOT teach CSS or theming fundamentals — instead it captures the iteration discipline when visual fixes don't stick on first attempt. Built on stdlib-only bash commands and Hermes file tools, no plugin dependencies.

## When to Use

- User complains about a specific theme issue ("Kreise unübersichtlich", "zu wenig Farben")
- A visual change worked but the user wants refinement
- Custom CSS snippets conflict with each other or with the active theme
- User feedback includes both rejection AND a direction ("mehr Unterteilungen", "weniger bunt")

## Prerequisites

- Active Obsidian vault with `.obsidian/snippets/` directory
- Backup folder convention established (`.obsidian.backup-<reason>-<ts>/`)
- Active theme documented in `.obsidian/appearance.json` (`cssTheme` field)
- Read access to `.obsidian/themes/<theme>.css` for class discovery
- `~/.hermes/skills/note-taking/obsidian/` for file operations

## How to Run

Invoke this skill when a visual fix doesn't satisfy the user. The loop runs as: `Backup → Mechanism-Discovery → Iterative Fix → Verify`. Each fix round takes ~5 minutes; budget 2-3 rounds.

## Quick Reference

| Step | Tool | Purpose |
|------|------|---------|
| Backup | `terminal` | `cp -a .obsidian .obsidian.backup-<reason>-<ts>/` |
| Find theme classes | `terminal` | `grep -E "body\.[a-z-]+\s*\{" .obsidian/themes/*.css` |
| Edit `app.json` | `patch` | patch `ignoredCssClasses` array |
| Add snippet | `write_file` | write to `.obsidian/snippets/<name>.css` |
| Force reload | user-side | `Ctrl+R` in Obsidian |

## Procedure

1. **Capture exact feedback verbatim.** Quote the user: "Kreise unübersichtlich, mehr Unterteilungen, 4 Farben zu wenig." Do not paraphrase into "user said it doesn't look good" — the verbatim carries direction, severity, and scope.

2. **Inventory current state.** Use `terminal` to read:
   - `ls .obsidian/snippets/` for active snippets
   - `.obsidian/appearance.json` for `enabledCssSnippets` and `cssTheme`
   - `.obsidian/app.json` for `ignoredCssClasses` and other settings

3. **Discover the theme's built-in disable mechanisms BEFORE writing CSS.** Many themes (Sanctum, ITS Theme, etc.) gate custom features behind body-classes like `body.no-<theme>-icons`. Find them all:
   ```bash
   grep -oE "body\.[a-z-]+" .obsidian/themes/<theme>.css | sort -u
   ```
   These classes are off-switches the theme respects unconditionally.

4. **Activate OFF-switches via `app.json`, not via CSS overrides.** Most theme-disable classes must go in:
   ```json
   {
     "ignoredCssClasses": ["no-sanctum-icons", "no-<theme>-<feature>"]
   }
   ```
   Patch `.obsidian/app.json` with `mode='replace'`. CSS-only attempts to disable theme features often fail because theme rules use `:not(.no-sanctum-icons)` selectors that only respond to body-class presence, not CSS specificity.

5. **Add CSS defense-in-depth as a fallback.** Even after activating the OFF-switch, write a CSS snippet that targets the same elements with `display: none !important`. This catches theme updates that re-enable the feature without warning. Snippet content:
   ```css
   body .theme-feature-selector { display: none !important; }
   ```

6. **Escalate visual granularity when feedback says "mehr" or "weniger".** Round progression:
   - Round 1: 4-5 distinct colors with simple border-left
   - Round 2: 8-10 colors + unique Unicode marker per category (✦ ⚑ ◆ ✿ ❖)
   - Round 3: 14+ markers with tree-style indentation (`├─ `, `│  · `, `└─ `)

7. **Pair color with Unicode markers.** Color alone fails for colorblind users and gets lost in dark-mode contrast shifts. Always combine:
   - Color (for mood)
   - Unicode marker (for shape recognition)
   - Background gradient (for hierarchy)
   - Bold weight (for emphasis)

8. **Layer visual hierarchy distinctly per depth level.** Top-level → Sub-level → Files each get distinct treatment:
   - Top: 4px solid border + linear-gradient background + bold + Unicode marker
   - Sub: 3px solid border + subtle background + monospace `├─ ` prefix
   - Files: 2px dashed border or tree-line `│  · ` prefix

9. **Document each iteration in a Snippet-Liste.md file.** Add new version entries containing:
   - What feedback triggered this version (verbatim quote)
   - What files changed and why
   - The next user-side action (`Ctrl+R` to see effect)

10. **Take a fresh backup per iteration.** Do not reuse backup folders. Use timestamp + reason suffix:
    ```bash
    BACKUP_DIR=".obsidian.backup-visualfix-$(date +%Y%m%d_%H%M%S)"
    cp -a .obsidian "$BACKUP_DIR"
    ```

## Pitfalls

- **CSS-only override of theme features often fails.** Many theme classes are gated by `:not(.no-<feature>)` selectors. Check `app.json: ignoredCssClasses` first, always.

- **Obsidian's CSS engine does not support `:has-text()`.** Use exact path selectors (`data-path="01 Kontext"`) and parent-child selectors (`.nav-folder:has(.nav-folder-title[data-path="..."])`) instead of `:has-text()` pseudo-classes.

- **First fix is rarely sufficient.** Visual iteration is rarely one-shot. Budget for 2-3 rounds and plan a backup before each iteration, not just at the start.

- **Backup folders accumulate.** Clean stale ones per phase. Naming convention: `phase5-*`, `phase6-*`, `visualfix-<ts>`.

- **Snippet load order matters.** Variables and color definitions must appear first in `enabledCssSnippets`. Override snippets go after the base snippets.

- **`Ctrl+R` is required, not optional.** Obsidian caches snippets aggressively. Without force-reload the user sees stale CSS even after file changes are written.

- **Mnemosyne hooks per iteration.** Save the feedback quote, the fix version, and the resulting snippet count as one `mnemosyne_remember` call per iteration. Lets future sessions recall what worked.

## Verification

After each iteration, confirm the loop is closed:

```bash
# Backup exists for the version that fixed it
ls /home/bratan/Dokumente/"Obsidian Vault"/.obsidian.backup-visualfix-*/ -d | tail -1

# Disabled theme class is active
cat /home/bratan/Dokumente/"Obsidian Vault"/.obsidian/app.json | grep -A2 ignoredCssClasses

# Snippet count and CSS-validity
ls /home/bratan/Dokumente/"Obsidian Vault"/.obsidian/snippets/*.css | wc -l
for f in /home/bratan/Dokumente/"Obsidian Vault"/.obsidian/snippets/*.css; do
  o=$(grep -o '{' "$f" | wc -l); c=$(grep -o '}' "$f" | wc -l)
  [ "$o" = "$c" ] || echo "UNBALANCED: $f ($o/$c)"
done

# Document iteration in Snippet-Liste.md
grep -A2 "Iteration" /home/bratan/Dokumente/"Obsidian Vault"/05\ Ressourcen/Snippet-Liste.md
```

The loop is complete when:
- The user can articulate what specifically improved (verbal confirmation)
- A backup exists for the version that fixed the issue
- `Snippet-Liste.md` documents the iteration trigger and resolution
- All CSS files have balanced braces
- `mnemosyne_remember` recorded the feedback→fix→resolution chain