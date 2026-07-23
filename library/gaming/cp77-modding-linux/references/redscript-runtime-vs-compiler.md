# REDscript: Compiler vs. Runtime-Plugin

Das REDscript-GitHub-Repo (`jac3km4/redscript`) enthält **NUR den CLI-Compiler** (`scc.exe` + `scc_lib.dll`), der `.reds`-Dateien nach `redscripts.cache` übersetzt. Er wird automatisch von ArchiveXL/TweakXL während ihrer Initialisierung verwendet.

Das **REDscript Runtime-Plugin** (`redscript.dll`) ist ein **separates RED4ext-Plugin**, das zur Laufzeit benutzerdefinierte `.reds`-Skripte lädt. Es ist **NICHT auf GitHub** verfügbar — nur auf Nexus Mods (ID 1511).

| Komponente | Quelle | Funktion |
|---|---|---|
| `scc.exe` (Compiler) | GitHub `jac3km4/redscript` | Kompiliert .reds zu Cache |
| `redscript.dll` (Runtime) | **NUR Nexus Mods #1511** | RED4ext-Plugin für custom .reds |
| `final.redscripts` | Game-Root `r6/cache/` | Fertig kompilierter Cache (vom Game selbst) |

**Konsequenz:**
- ArchiveXL/TweakXL laden **ohne** Runtime-Plugin trotzdem — sie bringen eigene .reds mit
- NG+ Native oder jede Mod, die `red4ext/plugins/redscript/` erwartet, braucht das Runtime-Plugin von Nexus
- Wenn `redscript/redscript.dll` im Plugin-Ordner fehlt, laden Mods mit `.reds`-Logik einfach nicht — **kein Crash, kein Error-Log**

**Installation (falls benötigt):**
```bash
# Manueller Download von Nexus Mods #1511
# Entpacken nach:
#   cyberpunk-2077/red4ext/plugins/redscript/redscript.dll
```