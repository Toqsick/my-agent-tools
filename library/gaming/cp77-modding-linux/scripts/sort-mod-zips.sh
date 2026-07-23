#!/bin/bash
# sort-mod-zips.sh — Sortiert ZIPs aus einem Quellordner ins CP77 Game-Root
# Erkennt automatisch: .archive → archive/pc/mod/, .dll → red4ext/plugins/<name>/, etc.
#
# Verwendung:
#   ./sort-mod-zips.sh [QUELL_ORDNER]
#   Default: ~/cp77-modding/downloads/

set -euo pipefail

CP77_ROOT="/home/bratan/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/Cyberpunk 2077"
CP77_PFX="/home/bratan/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/compatdata/1091500/pfx"
DOWNLOADS="${1:-$HOME/cp77-modding/downloads}"
LOG="$HOME/cp77-modding/sort-mod-zips.log"

mkdir -p "$DOWNLOADS"
: > "$LOG"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

# Sanity-Check
if [ ! -d "$CP77_ROOT" ]; then
    log "❌ CP77_ROOT existiert nicht: $CP77_ROOT"
    exit 1
fi

if [ ! -d "$CP77_ROOT/archive/pc/mod" ]; then
    log "❌ archive/pc/mod fehlt — Framework nicht installiert?"
    exit 1
fi

# Counter
total=0
archive_count=0
plugin_count=0
skipped=0

for zip in "$DOWNLOADS"/*.zip; do
    [ -f "$zip" ] || continue
    total=$((total+1))
    name=$(basename "$zip" .zip)

    # Mod-Ordner-Name: sicher (nur alphanumeric + _ -)
    mod_dir=$(echo "$name" | sed 's/[^a-zA-Z0-9_-]/_/g' | head -c 50)

    log "Processing: $name.zip"

    # Entpacke in temp dir
    tmpdir=$(mktemp -d)
    if ! unzip -q "$zip" -d "$tmpdir" 2>/dev/null; then
        log "  ⚠️  unzip fehlgeschlagen — überspringe"
        skipped=$((skipped+1))
        rm -rf "$tmpdir"
        continue
    fi

    # 1) .archive-Dateien → archive/pc/mod/ oder archive/pc/ep1/mod/
    archive_files=$(find "$tmpdir" -name "*.archive" -type f 2>/dev/null)
    if [ -n "$archive_files" ]; then
        # EP1-Erkennung: archive im Pfad oder "_ep1" im Namen
        if echo "$archive_files" | grep -q "ep1\|phantom"; then
            mkdir -p "$CP77_ROOT/archive/pc/ep1/mod"
            echo "$archive_files" | xargs -I {} cp {} "$CP77_ROOT/archive/pc/ep1/mod/"
            log "  → $(echo "$archive_files" | wc -l) .archive → archive/pc/ep1/mod/"
        else
            echo "$archive_files" | xargs -I {} cp {} "$CP77_ROOT/archive/pc/mod/"
            log "  → $(echo "$archive_files" | wc -l) .archive → archive/pc/mod/"
        fi
        archive_count=$((archive_count + $(echo "$archive_files" | wc -l)))
    fi

    # 2) RED4ext-Plugins (.dll + .lua + .yaml + .reds)
    plugin_files=$(find "$tmpdir" \( -name "*.dll" -o -name "*.lua" -o -name "*.yaml" -o -name "*.reds" \) -type f 2>/dev/null)
    if [ -n "$plugin_files" ]; then
        mkdir -p "$CP77_ROOT/red4ext/plugins/$mod_dir"
        echo "$plugin_files" | xargs -I {} cp {} "$CP77_ROOT/red4ext/plugins/$mod_dir/"
        log "  → $(echo "$plugin_files" | wc -l) Plugin-Files → red4ext/plugins/$mod_dir/"
        plugin_count=$((plugin_count + 1))
    fi

    # 3) Generischer Fallback: alles was übrig bleibt in eigenen Plugin-Ordner
    remaining=$(find "$tmpdir" -type f 2>/dev/null)
    if [ -z "$plugin_files" ] && [ -z "$archive_files" ] && [ -n "$remaining" ]; then
        mkdir -p "$CP77_ROOT/red4ext/plugins/$mod_dir"
        cp -r "$tmpdir"/* "$CP77_ROOT/red4ext/plugins/$mod_dir/" 2>/dev/null || true
        log "  → $(echo "$remaining" | wc -l) generische Files → red4ext/plugins/$mod_dir/"
        plugin_count=$((plugin_count + 1))
    fi

    rm -rf "$tmpdir"
done

log ""
log "=== Zusammenfassung ==="
log "ZIPs verarbeitet:    $total"
log ".archive-Dateien:    $archive_count"
log "Plugins installiert: $plugin_count"
log "Übersprungen:        $skipped"
log ""
log "Aktueller Stand:"
log "  archive/pc/mod:     $(ls "$CP77_ROOT/archive/pc/mod/" 2>/dev/null | wc -l) Dateien"
log "  archive/pc/ep1/mod: $(ls "$CP77_ROOT/archive/pc/ep1/mod/" 2>/dev/null | wc -l) Dateien"
log "  red4ext/plugins:    $(ls "$CP77_ROOT/red4ext/plugins/" 2>/dev/null | wc -l) Plugins"