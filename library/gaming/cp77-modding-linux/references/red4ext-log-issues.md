# RED4ext.log: Kann still fehlen

Selbst bei korrekter Installation schreibt RED4ext **unter Proton manchmal nie** ein `red4ext.log`. Das ist **kein** Zeichen für eine kaputte Installation — es kann an der DLL-Loading-Reihenfolge unter Proton liegen.

**Mögliche Ursachen (alle harmlos bis auf letzte):**
- REDlauncher intercepts DLL loading → RED4ext wird nicht initialisiert (`--launcher-skip` fix)
- Proton-Overlay blockiert DLL-Bootstrapping → CET/ASI-Loader initialisiert zu spät
- GE-Proton `version.dll` und `winmm.dll` kollidieren mit RED4exts eigenem Loader

**Symptome-Diagnose:**
```
KEIN red4ext.log    +   KEIN Cyberpunk2077.log   =  RED4ext nie geladen → --launcher-skip fehlt
KEIN red4ext.log    +   Cyberpunk2077.log OK      =  RED4ext geladen, aber silent → CET/ASI prüfen
red4ext.log VORHANDEN + geladen =  ✅ Alles korrekt
```

**Wenn kein Log kommt:** CET-Konsole (`~`) öffnen als alternativer Mod-Check. Wenn CET aufgeht, läuft alles. Wenn nicht, `--launcher-skip` prüfen oder REDlauncher.exe dummy verwenden.