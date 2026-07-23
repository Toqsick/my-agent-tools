# Pre-Launch Smoke-Check

Vor dem ersten Start nach Mod-Installation **alle** 12 Komponenten verifizieren:

```bash
# File-Checks (müssen existieren + > 1KB):
- red4ext/RED4ext.dll
- bin/x64/plugins/cyber_engine_tweaks.asi
- red4ext/plugins/ArchiveXL/ArchiveXL.dll
- red4ext/plugins/TweakXL/TweakXL.dll
- red4ext/plugins/Codeware/Codeware.dll

# Dir-Checks (müssen existieren):
- bin/x64/plugins/cyber_engine_tweaks/scripts/
- red4ext/plugins/ArchiveXL/
- red4ext/plugins/TweakXL/
- red4ext/plugins/Codeware/
- archive/pc/mod/
- archive/pc/ep1/mod/

# DLL-Konflikt-Check (keine doppelten Dateinamen):
find "$CP77_ROOT/red4ext" "$CP77_ROOT/bin/x64/plugins" \
    \( -name "*.dll" -o -name "*.asi" \) | \
    awk -F/ '{print $NF}' | sort | uniq -d
# Sollte leer sein.
```