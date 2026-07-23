# Pattern 0a: Pre-Flight Plan-Reality Check

## Problem
Das Briefing/der Plan enthält eine dateibasierte Spec (Pfade, Zeilenzahlen, Inhaltsangaben), aber die tatsächliche Vault-Struktur ist davon bereits abgewichen — z. B. weil eine frühere Session eine Datei verschoben hat, ohne den Plan zu aktualisieren.

## Symptom im Briefing
`05 Ressourcen/MOC - Daily Notes.md (0 Zeilen)` — aber die Datei liegt wirklich unter `/MOC - Daily Notes.md (0 Zeilen)` (root) oder existiert gar nicht.

## Lösung — vor Fan-Out IMMER ausführen

```python
# 1. JEDEN Pfad aus dem Plan gegen das echte Filesystem prüfen
for path in plan.paths:
    if os.path.exists(path):
        lines = wc_l(path)    # echte Zeilenzahl
        if lines != plan.lines:
            document_deviation(path, plan.lines, real_lines)
    else:
        search_files(target="files", pattern=basename(path), path=vault_root)
        # → gefundenen Pfad protokollieren; Plan muss korrigiert werden
        raise PlanRealityMismatch(f"{path} not found → alternatives: {search_results}")

# 2. Zero-Content vs. Nicht-Existenz disambiguieren
#    read_file(path) bei 0-Zeilen → gibt 0 lines zurück
#    terminal("wc -l path") → gibt "0" zurück
#    beides sagt NUR "exists but empty", nicht "doesn't exist"
#    Fehler von read_file(path) oder search_files sagt "doesn't exist"
#    → Stat: terminal("stat --format=%s path") → bei 0 bytes = truly empty file
```

## Ergebnis
Entweder Plan ist aktuell → weitermachen, oder Plan hat Stale-Einträge → korrigieren bevor ein Subagent ins Leere patcht.

## Praktisches Beispiel (Phase 6, 2026-07-05)
- **Plan sagte:** `05 Ressourcen/MOC - Daily Notes.md` — existierte nicht an diesem Pfad
- **Reality:** Die Datei lag in `/MOC - Daily Notes.md` (root) mit 0 Bytes / 0 Zeilen
- **Abweichung dokumentiert** und Improvisation-Permission (Pattern 6) für write_file auf dem korrekten Pfad genutzt