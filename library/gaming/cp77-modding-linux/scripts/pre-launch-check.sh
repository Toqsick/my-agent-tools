#!/usr/bin/env bash
# CP77 Pre-Launch Smoke-Check
# Prueft ob alle Frameworks vorhanden sind und keine Konflikte existieren.
# Output: 12/12 Komponenten OK = READY

set -uo pipefail

CP77_ROOT="/home/bratan/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/Cyberpunk 2077"

echo "==========================================="
echo " CP77 PRE-LAUNCH SMOKE-CHECK"
echo " $(date)"
echo "==========================================="
echo ""

declare -a CHECKS=(
    "FILE:red4ext/RED4ext.dll"
    "FILE:bin/x64/plugins/cyber_engine_tweaks.asi"
    "DIR:bin/x64/plugins/cyber_engine_tweaks"
    "DIR:bin/x64/plugins/cyber_engine_tweaks/scripts"
    "DIR:red4ext/plugins/ArchiveXL"
    "FILE:red4ext/plugins/ArchiveXL/ArchiveXL.dll"
    "DIR:red4ext/plugins/TweakXL"
    "FILE:red4ext/plugins/TweakXL/TweakXL.dll"
    "DIR:red4ext/plugins/Codeware"
    "FILE:red4ext/plugins/Codeware/Codeware.dll"
    "DIR:archive/pc/mod"
    "DIR:archive/pc/ep1/mod"
)

passed=0
total=0

for check in "${CHECKS[@]}"; do
    type="${check%%:*}"
    rel="${check##*:}"
    path="$CP77_ROOT/$rel"
    total=$((total+1))

    if [[ "$type" == "FILE" ]]; then
        if [[ -f "$path" ]]; then
            size=$(du -h "$path" | cut -f1)
            printf "  ✅ %-50s %s\n" "$rel" "$size"
            passed=$((passed+1))
        else
            printf "  ❌ %-50s FEHLT\n" "$rel"
        fi
    elif [[ "$type" == "DIR" ]]; then
        if [[ -d "$path" ]]; then
            count=$(find "$path" -maxdepth 1 -type f 2>/dev/null | wc -l)
            printf "  ✅ %-50s (%d files)\n" "$rel" "$count"
            passed=$((passed+1))
        else
            printf "  ❌ %-50s FEHLT\n" "$rel"
        fi
    fi
done

echo ""
echo "=== Plugin-DLL-Konflikt-Check ==="
dups=$(find "$CP77_ROOT/red4ext" "$CP77_ROOT/bin/x64/plugins" \
    \( -name "*.dll" -o -name "*.asi" \) 2>/dev/null | \
    awk -F/ '{print $NF}' | sort | uniq -d)
if [[ -z "$dups" ]]; then
    echo "  ✅ Keine doppelten Plugin-DLLs"
else
    echo "  ⚠️  Doppelte Dateinamen gefunden:"
    echo "$dups" | sed 's/^/      /'
fi

echo ""
echo "==========================================="
echo " ERGEBNIS: $passed / $total Komponenten OK"
if [[ $passed -eq $total ]]; then
    echo " STATUS: ✅ READY — Game kann gestartet werden"
    echo "==========================================="
    echo ""
    echo "Naechste Schritte:"
    echo "  1. Game ueber Steam starten (Flatpak)"
    echo "  2. Nach Ladebildschirm: ~ oder Insert tippen (CET-Konsole)"
    echo "  3. Tippe:        print('CET works')"
    echo "  4. Falls CET nicht oeffnet: siehe smoke-test-checklist.md"
    echo ""
    echo "Live-Log mitlesen:"
    echo "  tail -f \"$CP77_ROOT/red4ext.log\""
    exit 0
else
    echo " STATUS: ❌ NICHT READY — siehe fehlende Komponenten oben"
    echo "==========================================="
    exit 1
fi
