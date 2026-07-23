# CI-Bug NP-99 — ((BUILT++)) Exit-Code-Falle

## Symptom

`scripts/ci-build.sh` bricht nach 1 File ab, loggt "Build done" obwohl 65/66 Files nie gebaut wurden.

## Bug

`((BUILT++))` wirft Exit-Code 1 wenn `BUILT=0` (anfangs), unter `set -euo pipefail` terminiert das Script. Plus `2>/dev/null` schluckt alle greybel-Errors.

## Fix

```bash
# ALT (broken):
((BUILT++))

# NEU (correct):
((++BUILT)) || true

# stderr separat erfassen damit Fehler sichtbar bleiben:
err_log="$(mktemp)"
if "$GREYBEL" build "$f" "$target" 2>"$err_log"; then
    ((++BUILT)) || true
else
    echo "    ✗ $f"
    head -3 "$err_log" | sed 's/^/        /'   # erste 3 Zeilen für Debug
    ((++FAILED)) || true
fi
rm -f "$err_log"
```

## Lesson

In jedem Shell-Script das `set -euo pipefail` + Zähler hat: IMMER pre-increment (`++var`) mit `|| true` Wrapper, sonst unsichtbare Failure.