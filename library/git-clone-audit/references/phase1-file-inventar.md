# Phase 1 — File-Inventar Commands

```bash
# Source-Files nach Typ
find . -not -path './.git/*' -name '*.src' -type f | sort
find . -not -path './.git/*' -name '*.py'  -type f | sort

# Mit LOC
find . -not -path './.git/*' -name '*.src' -type f -exec wc -l {} + | sort -n

# Zweck aus Kopfzeilen
for f in $(find . -not -path './.git/*' -name '*.src' -type f | sort); do
  echo "--- $f ---"
  head -15 "$f" | grep -iE "^(// )?(description|name|version|author|purpose)"
done
```

**Output:** Tabelle mit Spalten: **Pfad | LOC | Zweck (1 Satz)**.