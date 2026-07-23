# MOC-Patch Verification

## Purpose

After editing a single MOC (Map of Content) — patching frontmatter, adding wiki-links, updating tables, or appending maintenance-log entries — verify that ALL wiki-links in the MOC resolve to existing vault files. This catches both **pre-existing dead links** (that predate your edit) and **new dead links** (typos in the links you just added).

## Detection vs. Fix

This workflow is **detection-only**. It finds dead links but does not fix them. The decision to fix a pre-existing dead link vs. a new one is a separate judgment call — a pre-existing dead link like `[[GreyHack - Scripting Libraries 2026-07-14]]` where the actual file is `GreyHack-Lib-Katalog-2026-07-14.md` (different naming convention) may need a different fix than a typo in a freshly added link.

## Methodology

### Step 1: Extract all wiki-links from the MOC

```bash
grep -oP '\[\[[^\]]+\]\]' /path/to/MOC.md | sort -u
```

This extracts every `[[Link Text]]` occurrence, deduplicates, and sorts alphabetically.

### Step 2: For each link, find the matching vault file

```bash
# For each `[[Link Text]]`:
# 1. Extract the basename (strip [[ ]] and any alias/path suffix)
# 2. Search the vault root for a .md file with exactly that basename (case-sensitive)
find /path/to/vault/ -name "*.md" -not -path "*/.obsidian/*" -not -path "*/.trash/*"
```

**Matching rules:**
- **Case-sensitive exact match** — Obsidian wiki-links are case-sensitive on Linux
- **Special characters matter** — em-dashes (`—`), ampersands (`&`), parentheses, commas, and spaces must match the actual filename exactly
- **Subfolder search** — vault files can be in any subfolder, not just the root. `find` searches recursively
- **Aliases** — if a file has an alias in its frontmatter, the wiki-link may match the alias instead of the filename. This is valid in Obsidian but harder to detect from the filesystem alone

### Step 3: Produce a verification table

Format the result as a sorted markdown table:

```
| Wiki-Link | Target-File existiert? | Pfad |
|---|---|---|
| [[GreyHack - Mission-Reports-Index-2026-07-14]] | ✅ | 04 Bereiche/Gaming/GreyHack - Mission-Reports-Index-2026-07-14.md |
| [[GreyHack - Scripting Libraries 2026-07-14]] | ❌ | NICHT GEFUNDEN |
| [[GreyHack-Tool-Workflow-CheatSheet-2026-07-14]] | ✅ | 09 System-Doku/GreyHack/GreyHack-Tool-Workflow-CheatSheet-2026-07-14.md |
```

### Step 4: Interpret the results

| Finding | Meaning | Next step |
|---|---|---|
| ✅ All 17 links resolve | MOC is clean, no dead links | Done |
| ❌ Dead link in a **newly added** wiki-link | Typo — fix the link in the MOC | Patch the MOC to correct the link text |
| ❌ Dead link in a **pre-existing** wiki-link | Pre-existing vault issue, not caused by this patch | Option A: Fix the link (rename file or change link text). Option B: Document as known issue, fix in a separate session |
| ❌ Link matches a file with slightly different naming convention | E.g., `[[GreyHack - Scripting Libraries 2026-07-14]]` vs `GreyHack-Lib-Katalog-2026-07-14.md` — the file exists but under a different convention | Decide: rename the file to match the link, or update the link to match the file |

## Pitfalls

| # | Pitfall | Mitigation |
|---|---|---|
| 1 | `grep` matches wiki-links inside code blocks or commented sections | Add `--` preamble before grep to limit to post-frontmatter content, or manually exclude code blocks |
| 2 | `find` with `-not -path "*/.obsidian/*"` still matches `.obsidian/`-adjacent files | Use `-not -path "*/.obsidian/*" -not -path "*/.trash/*"` |
| 3 | A file exists but with a different name (alias in frontmatter) | Cross-check with `grep -r "aliases:"` — the alias may be the intended target |
| 4 | Wiki-link with pipe/alias syntax `[[File|Display Text]]` | Strip the `|Display Text` suffix before matching |
| 5 | Wiki-link with section anchor `[[File#Section]]` | Strip the `#Section` suffix before matching |
| 6 | Case-insensitive filesystem (macOS) vs case-sensitive (Linux) | On Linux, `[[Note]]` will NOT match `note.md` — verify case |

## Script (one-liner for quick verification)

```bash
#!/bin/bash
# Quick MOC wiki-link verification
# Usage: ./verify-moc-links.sh <MOC.md> <vault-root>

MOC="$1"
VAULT="$2"
echo "| Wiki-Link | Status | Pfad |"
echo "|---|---|---|"
grep -oP '\[\[\K[^\]]+(?=\])' "$MOC" | sort -u | while read link; do
    # Strip alias and anchor
    clean="${link%%|*}"
    clean="${clean%%#*}"
    found=$(find "$VAULT" -name "*.md" -not -path "*/.obsidian/*" -not -path "*/.trash/*" | while read f; do
        base=$(basename "$f" .md)
        [ "$base" = "$clean" ] && echo "$f" && break
    done)
    if [ -n "$found" ]; then
        rel="${found#$VAULT/}"
        echo "| [[$link]] | ✅ | $rel |"
    else
        echo "| [[$link]] | ❌ | NICHT GEFUNDEN |"
    fi
done
```

## Key Insight

A sub-bee (leaf subagent) can perform this verification independently — it only needs read access to the MOC file and the vault. The sub-bee's output is a pure markdown table that the Queen can immediately interpret. This is a good candidate for sub-sub dispatch because the verification is isolated, mechanical, and produces a compact output that doesn't bloat the parent's context.

## Sub-Bee Briefing Template

```
Aufgabe: Wiki-Link-Target-Verifikation für MOC-Datei.

1. Lies <MOC.md> (nach dem Patch).
2. Extrahiere ALLE [[Wiki-Links]] aus der Datei (Regex: \[\[([^\]]+)\]\]).
3. Für jeden extrahierten Link: prüfe ob eine passende .md-Datei im Vault existiert.
   Suche mit find (case-sensitive) nach Dateien, deren Basename (ohne .md) exakt dem Link-Text entspricht.
4. Schreibe das Ergebnis als Markdown-Tabelle nach <output-path>.

Tabellen-Format:
```
| Wiki-Link | Target-File existiert? | Pfad |
|---|---|---|
| [[GreyHack]] | ✅ | 04 Bereiche/Gaming - GreyHack.md |
| [[NichtExistierend]] | ❌ | NICHT GEFUNDEN |
```

Sortiere alphabetisch nach Wiki-Link-Text.
```

## Proven

- 2026-07-14: GreyHack MOC, 17 unique wiki-links, 16 ✅ / 1 ❌ (pre-existing dead link detected)
- Dead link found: `[[GreyHack - Scripting Libraries 2026-07-14]]` — actual file is `GreyHack-Lib-Katalog-2026-07-14.md` (different date/naming convention)
- Cross-model sub-sub dispatch: Queen (GLM 5.2) → Worker (MiniMax-M3) → Leaf (MiniMax-M3), 42.84s wall time, 5 tool calls, sub_call_count=1