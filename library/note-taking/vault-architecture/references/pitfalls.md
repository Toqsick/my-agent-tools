# Pitfalls

## `_warning` field from `patch` tool — sibling subagent signal

When multiple agents edit the same vault folder concurrently, the `patch` tool returns an extra `_warning` field when a sibling subagent modified the target file since your last read:

```json
_warning: /path was modified by sibling subagent 'sa-...' at <time> — after this agent's last read at <time>. Re-read the file before writing.
```

**Critical distinction by signal case:**

| Case | What _warning means | Required action |
|---|---|---|
| **Patch succeeded + `_warning` present** (logged 2026-07-05: 2/7 files) | Patch landed against stale state. The sibling modified the file between your read and write. | **Mandatory:** re-read file immediately, verify total line count, section headers, and frontmatter integrity. |
| **Patch failed + `_warning` present** (classic case) | File changed so much that `patch` couldn't find the target string. | Re-read → re-identify anchor → re-patch. |
| No `_warning` | Either no sibling conflict, or no sibling touched this file. | Continue normally. |

**Required recovery pattern:**

1. **Re-read** the full file — don't trust the cached state from the first read.
2. **Re-identify** the edit target — the sibling may have changed the table structure, section format, or ordering.
3. **Re-patch** with the new target string matching the current file content.
4. **Watch for structural side-effects** — a patch on a table row can accidentally delete adjacent rows if the sibling restructured the table.

## `replace_all=true` can silently corrupt files

`replace_all=true` on the `patch` tool replaces **every** occurrence of the old_string in the file. This is dangerous when the pattern appears in slightly different contexts than you expect.

**Rules for safe replace_all:**
1. **Prefer unique-match `mode='replace'`** with enough context lines to distinguish the exact target — never use `replace_all` as a shortcut to avoid adding context
2. **If you must use `replace_all=true`**, first verify the exact number of occurrences: `grep -c '<unique-substring>' <file>`
3. **Verify immediately after** — re-read the full file section and check: no duplicate lines, expected line count, no orphan fragments

## Anti-halluzination: "manuell erweitern" date-stamp

Wenn du Vault-Notes mit quantitativen Daten befüllst und die Zahlen **nicht aus Live-Quellen oder existierenden Vault-Notes verifizieren kannst**:

1. **Keine erfundenen Performance-Zahlen.** Statt "~21.5 tok/s": `Je nach Modell (Stand YYYY-MM-DD, manuell erweitern).`
2. **Date-Stamp jeden quantitativen Wert** mit `**Stand YYYY-MM-DD, manuell erweitern wenn Tool-Doku erscheint.**`
3. **In der MOC-Quellen-Sektion** notieren, welche Datenquellen verfügbar waren.
4. **Grounded-Befehlssyntax ist OK** — NVML-Befehle, UFW-Policies, Whisper-Modellnamen sind stabil. Nur **Benchmark-Zahlen** nie ohne Quelle.

## Advisory voices can hallucinate factual claims

When using multi-voice self-review ("Advisor-Stimmen", "Rater" — simulated voices that review your own work), the generated voices can produce plausible-sounding but factually wrong claims about vault state.

**Mitigation — Ground-Truth Check before acting on any advisory claim:**

1. **Flag any factual claim** from an advisory voice as `🔎 unverified` in your notes — don't trust it because it "sounds right"
2. **Verify via terminal command** before incorporating into any output
3. **Cite the verification result** in the report (`✅` / `❌` with actual finding)
4. **Keep the verification command output** in your notes — if a voice later references the same claim, you have the correct answer

**Rule of thumb:** If 2+ advisory voices independently make the same factual claim, it's still unverified until you run the terminal command. Independent hallucination is not corroboration.

## Inline comment placeholders aren't script-filtered

The broken-link check script (`scripts/check-broken-wiki-links.py`) filters `<...>` style placeholder wiki-links via its `PLACEHOLDER_PATTERNS` regex. **Inline parenthetical comments like `(<-- Platzhalter, ...)` were NOT caught until 2026-07-05** — the regex only matched bracket-style `<...>` markers.

**Correct convention:** Use `<...>` for placeholder wiki-links that should not appear in the broken-link report:

```markdown
<!-- ✅ Will be filtered by script -->
- [[<Skript-Note>]]
- [[<Thumbnail-Pack>]]

<!-- ⚠️ Will NOT be filtered by older script versions -->
- [[Skript-Note]] (<-- Platzhalter, durch echte ersetzen)
```

## Post-expansion verification template

After every expansion phase, run the comprehensive verification script in `references/post-expansion-verification.md` to check:
- Each new note exists and has ≥ 3 wiki-links
- Patched hub notes mention the new topics (MOC/bereich references)
- Vault-wide link density is improving
- Consistency: new notes actually reference their parent MOC

Run this **after** the broken-link check — the script focuses on content quality, not broken-link detection.