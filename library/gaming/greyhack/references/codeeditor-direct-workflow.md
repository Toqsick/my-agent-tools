# CodeEditor-Direkt-Workflow

## Wann anwenden

Wenn eine `.src`-Datei bereits im Spiel-Dateisystem existiert (in `/home/gregor/Config/`), kann sie direkt im **CodeEditor geöffnet, bearbeitet und gebaut werden** — ohne erneute DB-Injection.

## Schritte im Spiel

1. **Computer → CodeEditor**
2. `Ctrl+O` (Open) → `/home/gregor/Config/<name>.src` auswählen
3. Source wird geladen → Neue Version aus Chat pasten (`Ctrl+A` → `Ctrl+V`)
4. `Ctrl+S` (Save)
5. **Build-Button** → Exe-Pfad `/bin/<name>`
6. `Close` → Zurück zur Shell → `<name>` eingeben

## Wann NICHT anwenden

**Nicht geeignet für:** Neue Dateien (dann DB-Injection für den ersten Eintrag, danach CodeEditor für Updates).

**Wann anwenden:** Immer wenn der Source bereits in Config/ liegt und nur aktualisiert werden muss. Kein DB-Edit, kein Backup nötig.