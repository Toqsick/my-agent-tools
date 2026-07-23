#!/usr/bin/env bash
# skill-curator-hygiene.sh — Three-File-Check + Reference-Inventur
# Usage: bash skill-curator-hygiene.sh [--brief|--full] [skill-path]
#        bash skill-curator-hygiene.sh [skill-path] [--brief|--full]
# Default: prüft alle Skills unter ~/.hermes/skills/

set -uo pipefail  # -e entfernt: sonst silent-failure bei grep/find no-match

# Argumente parsen — unterstützt beide Reihenfolgen
SKILL_ROOT="$HOME/.hermes/skills"
MODE="--full"
for arg in "$@"; do
    case "$arg" in
        --brief|--full) MODE="$arg" ;;
        /*) SKILL_ROOT="$arg" ;;
        *) SKILL_ROOT="$arg" ;;
    esac
done

echo "=== SKILL HYGIENE CHECK ==="
echo "Root: $SKILL_ROOT"
echo "Mode: $MODE"
echo

# 1. Reference-Inventur
echo "[1] Reference-Inventur pro Skill:"
DRIFT_COUNT=0
for skill_md in $(find "$SKILL_ROOT" -name "SKILL.md" -not -path "*/.archive/*"); do
    skill_dir=$(dirname "$skill_md")
    skill_name=$(basename "$skill_dir")
    mentioned=$(grep -oE 'references/[^`]+\.md' "$skill_md" 2>/dev/null | sort -u)
    actual=$(find "$skill_dir/references" -name "*.md" 2>/dev/null -printf "%f\n" 2>/dev/null \
             | sed 's|^|references/|' | sort -u)
    if [ -z "$actual" ] || [ -z "$mentioned" ]; then continue; fi
    if diff <(echo "$mentioned") <(echo "$actual") >/dev/null 2>&1; then
        [ "$MODE" = "--full" ] && echo "  ✅ $skill_name"
    else
        echo "  🚨 $skill_name — Reference-Drift"
        DRIFT_COUNT=$((DRIFT_COUNT + 1))
        [ "$MODE" = "--full" ] && diff <(echo "$mentioned") <(echo "$actual") | head -10
    fi
done
echo "  → $DRIFT_COUNT Skill(s) mit Reference-Drift"

# 2. Frontmatter-Pflichtfelder
echo
echo "[2] Frontmatter-Pflichtfelder (last_curated, trigger_keywords, agent):"
FIELD_MISSING_COUNT=0
for skill_md in $(find "$SKILL_ROOT" -name "SKILL.md" -not -path "*/.archive/*"); do
    skill_name=$(basename "$(dirname "$skill_md")")
    for field in "last_curated" "trigger_keywords" "agent"; do
        if ! grep -q "^${field}:" "$skill_md" 2>/dev/null; then
            echo "  🚨 $skill_name: fehlt '$field:'"
            FIELD_MISSING_COUNT=$((FIELD_MISSING_COUNT + 1))
        fi
    done
done
echo "  → $FIELD_MISSING_COUNT fehlende Pflichtfelder"

# 3. Three-File-Check (routing-table ↔ SKILL.md agent:)
ROUTING_TABLE="$HOME/.hermes/skills/orchestration/skill-navigator/references/routing-table.md"
if [ -f "$ROUTING_TABLE" ]; then
    echo
echo "[3] Three-File-Check (routing-table.md ↔ SKILL.md agent:):"
    grep -oP '`\K[a-z][-a-z]+(?=`)' "$ROUTING_TABLE" 2>/dev/null | sort -u | while read skill; do
        found=$(find "$SKILL_ROOT" -name "SKILL.md" -path "*/$skill/*" 2>/dev/null \
                | grep -v ".archive" | head -1)
        [ -z "$found" ] && echo "  ❌ $skill: kein SKILL.md" && continue
        if grep -q "^agent:" "$found" 2>/dev/null; then
            [ "$MODE" = "--full" ] && echo "  ✅ $skill"
        else
            echo "  🚨 $skill: KEIN agent:-Tag"
        fi
    done
else
    echo
echo "[3] Three-File-Check: SKIPPED (routing-table.md nicht gefunden)"
fi

echo
echo "=== DONE ==="
