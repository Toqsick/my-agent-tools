#!/usr/bin/env bash
# Hermes Disk-Cleanup — wöchentliche Platzfreigabe
# Läuft als no_agent Cron (tokenfrei)
# Pfad: ~/.hermes/scripts/disk-cleanup.sh

ALERTS=""
BEFORE=$(df / | awk 'NR==2 {print $5}' | tr -d '%')

# Hermes Logs älter 7 Tage löschen
find ~/.hermes/logs/ -name "*.log" -mtime +7 -delete 2>/dev/null

# Audio Cache leeren
rm -rf ~/.hermes/audio_cache/* 2>/dev/null

# Alte Config-Backups (nur letzte 3 behalten)
cd ~/.hermes 2>/dev/null || exit 0
ls -t config.yaml.bak.* 2>/dev/null | tail -n +4 | xargs -r rm -f

# state.db VACUUM (reduziert Fragmentierung)
if command -v sqlite3 &>/dev/null; then
    SIZE_BEFORE=$(du -sk ~/.hermes/state.db 2>/dev/null | cut -f1)
    sqlite3 ~/.hermes/state.db "VACUUM;" 2>/dev/null
    SIZE_AFTER=$(du -sk ~/.hermes/state.db 2>/dev/null | cut -f1)
    SAVED=$((SIZE_BEFORE - SIZE_AFTER))
    [ "$SAVED" -gt 0 ] && ALERTS+="🧩 state.db VACUUM: ${SAVED}KB frei\n"
fi

# Optional: pip cache leeren (nur wenn >500MB)
PIPCACHE=$(du -sm ~/.cache/pip 2>/dev/null | cut -f1)
[ "${PIPCACHE:-0}" -gt 500 ] && pip cache purge 2>/dev/null && ALERTS+="🧩 pip cache geleert\n"

AFTER=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
SAVED=$((BEFORE - AFTER))
[ "$SAVED" -gt 0 ] && ALERTS+="💡 Disk vorher ${BEFORE}% → jetzt ${AFTER}% (${SAVED}% frei)\n"

if [ -n "$ALERTS" ]; then
    echo -e "$ALERTS"
else
    echo "Disk-Cleanup: keine Änderung (vorher ${BEFORE}%, jetzt ${AFTER}%)"
fi
