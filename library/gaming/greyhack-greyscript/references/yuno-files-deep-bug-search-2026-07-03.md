# Deep Bug Search: yuno_files.src (2026-07-03)

## Metadaten

| Feld | Wert |
|------|------|
| Datei | `yuno_files.src` |
| Pfad | `config_modules/yuno_files.src` |
| Größe | 8,096 Bytes |
| Zeilen | 297 |
| Modul | YUNO V6 — ls, cat, get, put, rm, write, chmod, chown, ps, kill, passwd |
| Status | **0 Compiler-Bugs, 5 Runtime-Warnungen** |

## Geprüfte Pattern

### 1. Compiler-Pattern (8 Typen)

| Pattern | Ergebnis | Details |
|---------|----------|---------|
| String-in-String | ✅ Sauber | Keine `"text"inner"text"` Pattern |
| Komma-Bugs | ✅ Sauber | Keine trailing oder stray commas |
| Kommentare in Object-Literals | ✅ Sauber | Keine `//` zwischen `{` und `}` |
| Doppelte `//command:` Marker | ✅ Sauber | Nur 1 Marker auf Zeile 1 |
| `""""` Sequenzen | ✅ Sauber | Nicht vorhanden |
| Fehlende `end function`/`end if` | ✅ Sauber | 42 Block-`if` ↔ 42 `end if`; 12 functions ↔ 12 `end function`; 14 `{` ↔ 14 `}` |
| Zugewiesener Code ohne Init | ✅ Sauber | Alle 11 `cmd_X` haben `cmd_X = {}` Init |
| Body ohne Function Header | ✅ Sauber | Keine orphaned Bodies |

### 2. Runtime-Audit (Cross-Module)

| Check | Count | Severity | Details |
|-------|-------|----------|---------|
| `commands` undefined | 2 (Z. 291, 292) | 🔴 runtime | Dispatch-Block `commands.hasIndex(cmd)` + `commands[cmd].run()` — `commands` ist in dieser Datei nirgends definiert |
| `obj` undefined | 3 (Z. 86, 118, 279) | 🔴 runtime | `obj.host_computer.File()`, `obj.host_computer`, `obj.passwd()` — kein `obj = main_session.object` in dieser Datei |
| `main_session.*` gaps | 0 | ✅ | Alle Fields existieren im Core-Initializer |

## Lessons Learned

### 1. `obj` ist der #1 Lowercase-Variable-Bug

Im Gegensatz zu ALL-CAPS Symbolen wie `COMMON_PORTS` wird `obj` von keinem grep-basierten Scan erfasst, weil es wie eine normale lokale Variable aussieht. In yuno_files.src wird `obj` an 3 Stellen verwendet, aber nie initialisiert:

```bash
# yuno_core.src (Zeile 211):
obj = main_session.object

# yuno_files.src (Zeilen 86, 118, 279) — obj wird referenziert, aber NIEMALS zugewiesen
srcFile = obj.host_computer.File(srcPath)
remote_pc = obj.host_computer
obj.passwd(user, newpass)

# Fix: am Anfang des Moduls nach main_session-Zuweisung einfügen:
obj = main_session.object
```

**Detection:** Beim statischen Audit nach `obj.` (oder `pc.`/`shell.`) suchen, dann prüfen ob eine lokale `obj =` Zuweisung vorausgeht.

### 2. Compiler-Clean ≠ Runtime-Safe

Die Datei hat alle 8 Compiler-Patterns bestanden — strukturell einwandfrei, Balance perfekt. Trotzdem 5 garantierte Runtime-Crashes. **Immer Cross-Module Audit machen, auch wenn Compiler-Patterns sauber sind.**

## Vergleich: yuno_attack.src vs yuno_files.src

| Aspekt | yuno_attack.src | yuno_files.src |
|--------|----------------|----------------|
| Zeilen | 295 | 297 |
| Compiler-Bugs | 0 | 0 |
| Runtime-Bugs | 10 | 5 |
| Hauptmuster | ALL-CAPS missing + variable mismatch | `obj` + `commands` missing |
| Doppel-Guard | 2 dead code blocks | 0 |
