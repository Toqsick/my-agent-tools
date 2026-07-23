# Path Structure for CP77 Modding

```bash
# Flatpak Steam (Standardpath, z.B. Ubuntu + Flatpak Steam)
FLATPAK_STEAM="/home/bratan/.var/app/com.valvesoftware.Steam/.local/share/Steam"
CP77_ROOT="$FLATPAK_STEAM/steamapps/common/Cyberpunk 2077"

# Wine-Prefix (Proton compatdata)
CP77_PFX="$FLATPAK_STEAM/steamapps/compatdata/1091500/pfx"

# Windows-Saves-Pfad (unter Wine-Prefix!)
# **NICHT** unter ~/Documents/ — das existiert nur unter Windows!
SAVES_DIR="$CP77_PFX/drive_c/users/steamuser/Saved Games/CD Projekt Red/Cyberpunk 2077"
```

**Wichtig:** Saves liegen NICHT unter `~/Documents/` — das existiert nur unter nativem Windows. Die Saves sind nur im Wine-Prefix unter `drive_c/users/steamuser/Saved Games/CD Projekt Red/Cyberpunk 2077`.