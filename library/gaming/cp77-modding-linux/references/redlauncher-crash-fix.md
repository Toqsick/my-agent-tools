# REDlauncher Crash Fix (ESSENTIAL)

## Problem

REDlauncher crasht unter Proton/Steam-Play mit **ACCESS_VIOLATION**:

```
Exit Code: -1073741819 (0xC0000005 → STATUS_ACCESS_VIOLATION)
```

Die Ursache ist ein CDPR-GUI-Launcher (Qt-basiert), der unter Wine/Proton nicht richtig initialisiert. Folge: Game startet zwar (via REDprelauncher → REDupdater), aber der Launcher stürzt nach dem Game-Start ab, und REDmods-Qt-Prozesse schlagen ebenfalls fehl.

**Symptome:**
- Launcher-UI crash oder schwarzes Fenster
- `"Error during REDmod deploy command, Qt process error 'FailedToStart'"` im REDprelauncher.log (unvermeidbar unter Proton)
- `"Mods were found: false"` — da REDmod deploy crashed, ist der Status immer false
- REDmod-Toggle im Launcher ist ausgegraut/deaktiviert

**Wichtig:** Dieser Fehler betrifft NUR den Game-Launcher. Die eigentlichen Mod-Frameworks (RED4ext, CET, ArchiveXL, TweakXL, Codeware) laden via DLL-Injection unabhängig davon.

## Lösung: `--launcher-skip`

REDprelauncher.exe hat ein eingebautes Flag **`--launcher-skip`** (im Binary hard-coded, bestätigt via `strings`-Analyse). Es überspringt den REDlauncher GUI komplett und startet Cyberpunk2077.exe direkt.

**Steam Launch-Options editieren:**

```bash
# ALT (crasht):
LaunchOptions: "DXVK_FILTER_DEVICE_NAME=\"NVIDIA RTX...\" VKD3D_CONFIG=nodxr %command%"

# NEU (--launcher-skip hinzugefügt):
LaunchOptions: "DXVK_FILTER_DEVICE_NAME=\"NVIDIA RTX...\" VKD3D_CONFIG=nodxr --launcher-skip %command%"
```

**⚠️ Steam resetted LaunchOptions beim Beenden.** Steam überschreibt `localconfig.vdf` mit seinem internen Cache. Der Edit hält NICHT dauerhaft wenn Steam die Config zurückschreibt. Workarounds:

- **Nach jedem Edit:** Game sofort starten ohne Steam zwischenzeitlich zu schließen
- **Besser:** Vor Edit ein Backup der Datei machen + nach Edit die Datei auf read-only setzen:
  ```bash
  cp localconfig.vdf localconfig.vdf.backup
  chmod 444 localconfig.vdf  # read-only, Steam kann nicht überschreiben
  ```
  ⚠️ Read-only kann Steam-Updates blockieren — bei neuem CP77 Patch manuell revertieren:
  ```bash
  chmod 644 localconfig.vdf
  ```

## Fallback: REDlauncher.exe durch Dummy ersetzen

Wenn `--launcher-skip` nicht greift (Steam resetted trotzdem), gibt es einen robusteren Weg:

```bash
# REDlauncher.exe im Wine-Prefix weglegen
PRELAUNCHER_DIR="$CP77_PFX/drive_c/users/steamuser/AppData/Local/Programs/CD Projekt Red/REDlauncher"
cp "$PRELAUNCHER_DIR/REDlauncher.exe" ~/cp77-modding/backups/exe/REDlauncher.exe.original
mv "$PRELAUNCHER_DIR/REDlauncher.exe" "$PRELAUNCHER_DIR/REDlauncher.exe.real"
```

**Effekt:** REDprelauncher ruft REDlauncher.exe auf → Datei fehlt → REDprelauncher fällt auf Game-Direct-Start zurück. Das funktioniert auch ohne `--launcher-skip`.

**Empfohlene Kombination für maximale Zuverlässigkeit:**
1. `--launcher-skip` in Steam LaunchOptions setzen
2. REDlauncher.exe dummy ersetzen (mv → .real)
3. localconfig.vdf backup + read-only

Alle drei Schritte sind unabhängig voneinander — jeder alleine reicht, zusammen sind sie absolut.

**Position für Flatpak Steam** → `localconfig.vdf`:

```
~/.var/app/com.valvesoftware.Steam/.local/share/Steam/userdata/<user_id>/config/localconfig.vdf
```

Der Eintrag für CP77 (AppID 1091500) sieht so aus:

```
"1091500"
{
    "LaunchOptions" "DXVK_FILTER_DEVICE_NAME=\"NVIDIA GeForce RTX 5060 Laptop GPU\" VKD3D_CONFIG=nodxr RADV_PERFTEST=gpl --launcher-skip %command%"
}
```

**Backup-Pattern vor Edit:** Lokale `localconfig.vdf` kopieren, da Steam sie bei Reparatur überschreiben kann.

## Diagnose-Logs (wenn REDlauncher crasht)

| Log-Pfad | Inhalt |
|---|---|
| `$CP77_PFX/drive_c/users/steamuser/AppData/Local/CD Projekt Red/REDprelauncher/REDprelauncher.log` | REDprelauncher-Hauptlog |
| `$CP77_PFX/drive_c/users/steamuser/AppData/Local/CD Projekt Red/REDprelauncher/sessions/` | Session-Details pro Launch |
| Steam stdout (Terminal) | Steam-Output zeigt `0xC0000005` auf Exit |
| `$CP77_PFX/drive_c/users/steamuser/AppData/Local/CD Projekt Red/REDupdater/` | REDupdater-Logs |

Wine-Prefix-Pfad (compatdata):
```bash
CP77_PFX="$FLATPAK_STEAM/steamapps/compatdata/1091500/pfx"
```