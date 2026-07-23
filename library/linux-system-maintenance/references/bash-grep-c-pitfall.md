# Bash `grep -c` Multi-Line Integer-Comparison Pitfall

> **Gelernt 2026-07-17:** Beim agents-md-drift-check.sh Sanity-Test — `grep -c`
> gab mehrzeiligen Output zurück, der `[[ "$HITS" -gt 0 ]]` mit "Ganzzahliger
> Ausdruck erwartet" scheitern liess.

## Symptom

```bash
HITS=$(grep -c -F "pattern" file.txt)
# Wenn grep multiple inputs matched ODER stderr in stdout leakt:
# HITS="1\n0\n0"  statt  "HITS=1"
if [ "$HITS" -gt 0 ]; then
    # Bash: "./script.sh: Zeile 22: [: : Ganzzahliger Ausdruck erwartet"
```

## Root Cause

`grep -c` zählt Matches pro File. Wenn mehrere Files gematcht werden (auch via
Pipe oder wenn stderr nicht getrennt ist), gibt grep mehrzeiligen Output zurück:
`1\n0\n0`. Bash `-gt` erwartet einen einzelnen Integer, nicht einen String mit
Newlines.

## Fix

```bash
# Zwei-Schritt-Absicherung:
HITS=$(grep -c -F "pattern" file.txt 2>/dev/null | head -1 | tr -d ' \n')
HITS=${HITS:-0}
if [ "$HITS" -gt 0 ] 2>/dev/null; then
    echo "Gefunden"
fi
```

| Schritte | Was es macht | Warum |
|----------|-------------|-------|
| `2>/dev/null` | stderr unterdrücken | Keine "binary file matches" Warnungen |
| `head -1` | Nur erste Zeile | Selbst bei Multi-File die verwertbare Zeile |
| `tr -d ' \n'` | Whitespace+Newline entfernen | Bash `-gt` akzeptiert nur bare integer |
| `${HITS:-0}` | Fallback auf 0 | Wenn `grep` gar keinen Output produziert |
| `2>/dev/null` im Test | `-gt` Fehler unterdrücken | Falls doch ein nicht-integer durchrutscht |

## Oder: Python verwenden (robuster)

```python
import subprocess
result = subprocess.run(["grep", "-c", "-F", "pattern", "file.txt"],
                       capture_output=True, text=True)
count = int(result.stdout.strip().split("\n")[0]) if result.stdout else 0
```

## Wann anwenden

- IMMER wenn `grep -c` in Bash `if`-Statements verwendet wird
- Besonders wenn `2>/dev/null` fehlt (stderr kann zusätzliche Zeilen einstreuen)
- Bei Multi-File-Grep (`grep -c pattern file1 file2`) IMMER
- Als Faustregel: `grep -c` in Bash ist fehleranfällig ab >1 Input-Stream

## Siehe auch

- `linux-system` → "Common Bash Bugs" #9: `grep -c` trailing newline
- `linux-system-maintenance` → "Full System Audit Lifecycle" Phase 1 Pitfall
