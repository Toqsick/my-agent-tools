# Saves-Backup aus der Wine-Prefix

```bash
# Backup-Befehl (tar direkt aus der Wine-Prefix)
CP77_PFX="/home/bratan/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/compatdata/1091500/pfx"
SAVES_DIR="$CP77_PFX/drive_c/users/steamuser/Saved Games/CD Projekt Red/Cyberpunk 2077"
BACKUP="$HOME/cp77-modding/backups/saves-$(date +%Y%m%d-%H%M%S).tgz"

mkdir -p "$(dirname "$BACKUP")"
tar czf "$BACKUP" -C "$SAVES_DIR" .
echo "Saves gesichert: $BACKUP"
```

Retention: nur die letzten 3 Backups behalten (`ls -t | tail -n +4 | xargs rm -f`).