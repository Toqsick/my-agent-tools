# Launcher.INI: ModsEnabled erzwingen

Auch mit `--launcher-skip` kann der Launcher-INI-Eintrag `UserGameModsEnabled` auf `false` stehen bleiben. Das verhindert zwar keine DLL-Injection, aber der REDprelauncher loggt dann immer `"Mods were found: false"`.

**Fix:** `launcher.ini` editieren — liegt **im Wine-Prefix**, nicht im Game-Root:

```bash
LAUNCHER_INI="$CP77_PFX/drive_c/users/steamuser/AppData/Local/Programs/CD Projekt Red/REDlauncher/config/launcher.ini"

# Vorher:
# [UserGameModsEnabled]
# 3568394505849003\cyberpunk2077=false

# Nachher:
sed -i 's/cyberpunk2077=false/cyberpunk2077=true/' "$LAUNCHER_INI"
```

**Verifikation nach Edit:**
```bash
grep -A2 'UserGameModsEnabled' "$LAUNCHER_INI"
# Erwartet: 3568394505849003\cyberpunk2077 = true
```

Beachte: Der Wert wird beim nächsten REDlauncher-Start evtl. wieder auf `false` gesetzt. Wenn du `--launcher-skip` verwendest (REDlauncher läuft nie), bleibt der Wert erhalten.