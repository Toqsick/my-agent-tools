#!/usr/bin/env bash
# Wiki-Link Density Check — portable shell-based verification
# Usage: ./wiki-link-density.sh <vault-path> [file ...]
#   If files given, check only those (relative to vault-path)
#   If no files, scan entire vault (skipping .obsidian .trash .git)
# Output: per-file stats sorted by link count descending + aggregate summary
set -euo pipefail

VAULT="${1:?Usage: $0 <vault-path> [file ...]}"
shift

if [ ! -d "$VAULT" ]; then
    echo "ERROR: Vault path '$VAULT' does not exist" >&2
    exit 1
fi

declare -a file_results=()
total_files=0 total_links=0
lowest_links=99999 lowest_file=""

collect() {
    local path="$1" rel="$2"
    local lines links
    lines=$(wc -l < "$path" 2>/dev/null || echo 0)
    lines=${lines// /}
    links=$(grep -oE '\[\[[^\]][^\]*\]\]' "$path" 2>/dev/null | wc -l || echo 0)
    links=${links// /}
    file_results+=("${lines}|${links}|${rel}")
    total_files=$((total_files + 1))
    total_links=$((total_links + links))
    if [ "$links" -lt "$lowest_links" ]; then
        lowest_links=$links
        lowest_file="$rel"
    fi
}

if [ $# -gt 0 ]; then
    for f in "$@"; do
        fp="$VAULT/$f"
        [ -f "$fp" ] && collect "$fp" "$f" || echo "WARN: $fp not found" >&2
    done
else
    while IFS= read -r -d '' md; do
        rel="${md#$VAULT/}"
        case "$rel" in .obsidian/*|.trash/*|.git/*) continue;; esac
        collect "$md" "$rel"
    done < <(find "$VAULT" -name '*.md' -type f -print0)
fi

# Sort descending by link count
echo "=== Per-File Wiki-Link Density ==="
IFS=$'\n' sorted=($(sort -t'|' -k2 -rn <<<"${file_results[*]}"))
unset IFS
for line in "${sorted[@]}"; do
    IFS='|' read -r lnk sz name <<< "$line"
    printf "%3d links | %3d lines | %s\n" "$lnk" "$sz" "$name"
done

echo
echo "=== Aggregate ==="
echo "Files: $total_files  Total links: $total_links"
[ $total_files -gt 0 ] && \
    printf "Avg: %.1f  Lowest: %d (%s)\n" \
    "$(echo "scale=1; $total_links / $total_files" | bc)" \
    "$lowest_links" "$lowest_file"
