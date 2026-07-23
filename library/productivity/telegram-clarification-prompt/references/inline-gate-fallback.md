# Inline Gate Fallback (Telegram Tool Unavailable)

## When to Use This Pattern

- `send_message`/`telegram` tool is NOT available (check first)
- Basti is actively in the same chat
- Decision requires 2-4 concrete options

## When NOT to Use

- Basti explicitly asked for Telegram ("schreib mir auf Telegram")
- Task blocks entirely and user may not be watching
- Decision tree has 5+ branches

## Required: Pattern-7 Verification BEFORE the Gate

Advisor voices (multi-voice self-review) hallucinated 4/4 factual claims during Phase 10 planning:

| Voice claim | Ground truth |
|---|---|
| "Glossar fehlt / ist zu kurz" | ✅ 265 Zeilen, 18.4 KB, ~95% linked |
| "baseSize: 12 — absurd" | ✅ Kein baseSize-Key, nodeSizeMultiplier: 0.8 |
| "Graph-Farben alle schwarz" | ✅ 16 colorGroups mit RGB-Werten |
| "08 Anhaenge/ fehlt" | ✅ Existiert (leer: nur _README) |

**Always run these verification commands before gate:**
```bash
wc -l <vault>/05\ Ressourcen/Glossar.md 2>/dev/null || echo "missing"
grep baseSize <vault>/.obsidian/graph.json 2>/dev/null || echo "no baseSize"
ls <vault>/.obsidian/plugins/ 2>/dev/null || echo "plugins/ missing"
ls <vault>/08\ Anhaenge/
```

## Inline Gate Structure

```
## 🔴 Befund: [Pattern-7 verified fact]

[Sachliche Wahrheit]

## [2-4 Optionen]

A — [Option] ([rationale])
B — [Option] ([rationale])

## Was ich vorschlage

1. [Safe additive action I can start now]
2. Warten auf deine Entscheidung: A/B/C
```

## Pro Example (Phase 10)

```
## 🔴 Befund 1: Obsidian läuft (PIDs 65503, 65506)
## 🔴 Befund 2: Anhänge-b würde 15+ Wiki-Links brechen

A — Sub-Struktur anlegen, im Schema bleiben ⭐
B — Ordner löschen + mass-replacen
C — Hybrid: Schema bleibt, README zu 05 Ressourcen/_templates/

1. Obsidian killen (du machst)
2. Block 1 sofort (additiv, reversibel)
3. Warten auf Entscheidung A/B/C
```

## Critical Rule

**Inline Gate ≠ Inline Frage.** Inline Gate is structured with 2-4 options and a recommendation. Inline Frage is vague ("Was meinst du?"). Always use the Gate format when falling back.
