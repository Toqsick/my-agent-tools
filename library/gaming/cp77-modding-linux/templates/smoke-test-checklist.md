# CP77 Modding — Erster Smoke-Test

> Checkliste für den allerersten Game-Start **nach** Framework-Installation.
> Führe vorher `bash scripts/pre-launch-check.sh` aus.

## Vorbereitung

- [ ] Pre-Launch-Check durchgeführt (12/12 grün)
- [ ] **`--launcher-skip` in Steam Launch-Options gesetzt?** (sonst REDlauncher-Absturz unter Proton mit `0xC0000005`)
  - Falls Steam Option resetted: `chmod 444 localconfig.vdf` nach Edit
- [ ] **REDlauncher.exe durch Dummy ersetzt?** (optional, als Fallback)
  - `REDlauncher.exe.real` vorhanden? Sonst: `mv REDlauncher.exe REDlauncher.exe.real`
- [ ] **launcher.ini ModsEnabled geprüft?** (s.o.)
  - `cyberpunk2077 = true` in `[UserGameModsEnabled]`
- [ ] Zweites Terminal offen für Live-Logs
- [ ] GE-Proton Version notiert: ___________

## Live-Log vorbereiten

```bash
# RED4ext-Mod-Injection (Game-Root)
tail -f "/home/bratan/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/Cyberpunk 2077/red4ext.log"

# REDprelauncher.log (Primary Source für Launcher-Probleme)
CP77_PFX="/home/bratan/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/compatdata/1091500/pfx"
tail -f "$CP77_PFX/drive_c/users/steamuser/AppData/Local/CD Projekt Red/REDprelauncher/REDprelauncher.log"
```

> **Hinweis:** RED4ext.log wird unter Proton manchmal nie geschrieben (silent failure). In dem Fall ist CET-Konsole `~` der bessere Mod-Check.

## Game starten

1. Steam öffnen (Flatpak)
2. Cyberpunk 2077 starten
3. Warten bis Hauptmenü-UI sichtbar (~30s-60s)

## Im Hauptmenü — Mod-Load prüfen

- [ ] **RED4ext-Log checken:** Im zweiten Terminal gelesen?
  - ✅ `[RED4ext] Plugin ArchiveXL loaded`
  - ✅ `[RED4ext] Plugin TweakXL loaded`
  - ✅ `[RED4ext] Plugin Codeware loaded`
  - ✅ `[RED4ext] Initialization complete`
  - ❌ Bei ERROR/FATAL-Output: siehe Troubleshooting

- [ ] **CET-Konsole öffnen:** `~` (Tilde) getippt?
  - ✅ Konsole öffnet sich oben im Overlay
  - ❌ Nichts passiert → Insert-Taste probieren
  - ❌ Auch nix → GE-Proton-Version checken

## CET-Konsole — Quicktest

```lua
print("CET works")           -- Sollte "CET works" im Konsolen-Fenster zeigen
Game.GetVersion()              -- Zeigt Game- + CET-Version
```

- [ ] `print("CET works")` gab Echo? → ✅ CET läuft
- [ ] `Game.GetVersion()` zeigte Version? → ✅ Game + CET erkennbar

## Nächste Schritte nach Smoke-Test

| Ergebnis | Was tun |
|---|---|
| ✅ Alles geladen | Mods installieren! NG+ Native + redscript + Mod Settings |
| ✅ CET geschlossen (ESC) | Game läuft sauber ohne dich |
| ❌ RED4ext ERROR | Versions-Konflikt → neueste Versionen checken |
| ❌ CET-Konsole tot | GE-Proton downgraden auf 9-7, dann nochmal |
| ❌ Game-Crash sofort (Exit Code -1073741819) | `--launcher-skip` fehlt in Launch-Options → ergänzen (siehe SKILL.md) |
| ❌ REDmod-Toggle deaktiviert/ausgegraut | **NORMAL unter Proton** — Qt-Tool crasht, Mods laden trotzdem via DLL-Injection |
| ❌ "Mods were found: false" im Log | Ebenfalls normal — REDmod deploy crashed vor dem Scan; RED4ext/CET laden trotzdem |
| ❌ Weder RED4ext.log noch CET-Log | RED4ext kann silent failen → CET-Konsole `~` prüfen oder `--launcher-skip` + REDlauncher-Dummy |
| ❌ REDlauncher startet trotz --launcher-skip | Steam hat LaunchOptions resetted → Dummy-Ersatz (mv REDlauncher.exe → .real) als Fallback |
| ❌ `launcher-skip` verschwindet nach Steam-Neustart | Steam überschreibt localconfig.vdf → `chmod 444 localconfig.vdf` nach Edit |
