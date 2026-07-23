# Framework Dependency Order

Diese Reihenfolge MUSS eingehalten werden (lower = Foundation, higher = baut auf):

1. **RED4ext** — Script-Host-Loader (.dll Injections)
2. **CET** — Lua-Konsole + Plugin-Host (.asi Loader)
3. **ArchiveXL** — .archive Mod-Loader (braucht RED4ext)
4. **TweakXL** — .yaml Tweak-Loader (braucht RED4ext)
5. **Codeware** — C# Modding-Shim (braucht RED4ext)
6. **redscript** — Lua-Erweiterungen (optional, braucht RED4ext)
7. **Mod Settings** — GUI für Mod-Konfiguration (braucht Codeware)

**Redscript** und **Mod Settings** sind nur für Mods mit .lua-Skripten nötig. NG+ Native (Nexus ID 15043) braucht beides.