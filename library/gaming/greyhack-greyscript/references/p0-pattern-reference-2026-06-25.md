# P0-Pattern Auto-Fix Reference (2026-06-25)

> Auto-Fix Strategie für Bulk-P0-Cleanup. Verified 2026-06-25, 81 Fixes in 13 Files.
> Referenziert aus SKILL.md "Auto-Fix Strategie für Bulk-P0-Cleanup".

## Workflow

Wenn ein Daily-Scan 30+ P0-Findings in ein paar Pattern-Clustern produziert, **nicht manuell fixen**. Das lohnt sich erst ab ~5 Files pro Cluster. Stattdessen:

1. **Pattern erkennen + clustern** — die meisten Findings sind in 3-5 Clustern (z.B. `Negativer Index`, `Einzeiliges if/then/end if`, `"char(10)"` als String).
2. **Regex-Auto-Fixer schreiben** (~30 Zeilen Python, idempotent, dry-run-fähig). Persistieren unter `scripts/fix-p0-patterns.py` oder als neue Datei in `scripts/` — **nicht** in `/tmp` lassen.
3. **Pro Pattern eine eigene `fix_*()` Funktion** — der Fixer wächst mit den Patterns.
4. **Lokal verifizieren** mit `greybel build <file.src> /tmp/out` für jedes File, **bevor** CI gepusht wird.
5. **Erst dann PR** mit Validation-Report im Body (Build-Output + Lint-Output beilegen).

## Auto-Fix-Recipes (Stand 2026-06-25, 81 Fixes in 13 Files)

| Pattern | Regex (Python) | Action |
|---------|---------------|--------|
| Single-line `if X then Y end if` | `r'^([ \t]+)(if\b.+?\bthen\b)(.+?)(\bend if\b)\s*$'` | Expand zu multi-line Block mit zusätzlichem `\t` Indent für BODY |
| `=======` Separator | `r'^=+\s*$'` | Zeile löschen (oder `// =` davor) |
| `print("...\""...)` | replace-all mit single-quote Variante | siehe `scripts/fix-p0-patterns.py` `fix_setup_escape()` |

## Vorher / Nachher Beispiele

### Single-line `if ... then ... end if`

Vorher:
```
if x > 0 then print("ok") end if
```

Nachher:
```
if x > 0 then
	print("ok")
end if
```

### `=======` Separator

Vorher:
```
print("==================")
print("Header")
```

Nachher:
```
// ==================
print("Header")
```

### Backslash-Escape in `print`

Vorher:
```
print("  importcode(\"bin/X.src\")")
```

Nachher:
```
print("  importcode('bin/X.src')")
```

## Pitfall: Idempotenz

Auto-Fixer muss das Idempotenz-Kriterium erfüllen — eine schon-validierte Datei darf beim zweiten Lauf nicht anders aussehen. Test mit Pattern, das schon multi-line ist: `if X then\n\tY\nend if` darf nicht erneut transformiert werden.

## Verwandte Referenzen

- `references/build-ci-fix-2026-06-19.md` — Batch-Fix für one-line-ifs + ternäre Ausdrücke + CI-Build 18/18 sauber
- `references/build-pipeline-ci-quirks.md` — greybel `-u` flag parser strictness, CI script behavior, build order, and `-dbf` output layout
- `references/language-pitfalls.md` — vollständige Liste der Compile-Zeit-Fallen
