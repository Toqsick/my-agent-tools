#!/bin/bash
# bug-scan-pattern-audit.sh
# Static-Scan + Build-Verifikation für GreyScript (.src) Repos.
# Reproduces the 14-pattern audit + 5-category build-fail classification
# proven in the 2026-07-07 multi-agent bug-sweep (PR #56 + #57 merged to main).
#
# Usage:
#   bash bug-scan-pattern-audit.sh [--src-dir DIR] [--patterns-only] [--build-only]
#
# Default src-dir: . (current repo root)
# Patterns-only: skip the greybel build step (faster, no dependencies needed)
# Build-only: skip the static-scan step

set -euo pipefail

SRC_DIR="${SRC_DIR:-.}"
SCAN_ONLY=0
BUILD_ONLY=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --src-dir) SRC_DIR="$2"; shift 2 ;;
        --patterns-only) SCAN_ONLY=1; shift ;;
        --build-only) BUILD_ONLY=1; shift ;;
        -h|--help)
            grep -E "^# " "$0"
            exit 0
            ;;
        *) echo "Unknown arg: $1" >&2; exit 1 ;;
    esac
done

cd "$SRC_DIR"

# === STEP 1: Static-Scan (14 Patterns) ===
if [[ "$BUILD_ONLY" -eq 0 ]]; then
    echo "=== STEP 1: Static-Scan (14 Patterns) ==="
    
    # Filter active .src files (excluded: tests/, imports/, build/, greybel-vs/, .ci-build/)
    mapfile -t FILES < <(git ls-files '*.src' 2>/dev/null \
        | grep -v -E "^(tests/|imports/|build/|greybel-vs/|\.ci-build/)" \
        | sort)
    
    if [[ ${#FILES[@]} -eq 0 ]]; then
        echo "  ⚠️  No .src files found. Use --src-dir to point to a greyhack-tools repo."
        exit 1
    fi
    
    echo "  Files in scope: ${#FILES[@]}"
    
    declare -A PATTERNS=(
        ["(a) one-line-if/then/end if"]='\bif\b.*\bthen\b.*\bend\s+if\b'
        ["(b) ternary X if C else Y"]='\bif\b.*\belse\b'
        ["(c) \\n statt char(10)"]='\\n'
        ["(d) single-quote 'text' in CODE"]="'[^']*'"
        ["(e) inline-if assignment"]='=\s*\(.*\bif\b.*\belse\b'
        ["(f) \\ in strings"]='\\"'
        ["(g) === separator line"]='^=+\s*$'
        ["(h) [^N] negative index"]='\[\^-?\d+\]'
        ["(i) .strip()/.trim()"]='\.(strip|trim)\b'
        ["(j) str_repeat"]='\bstr_repeat\b'
        ["(k) get_system_time"]='\bget_system_time\b'
        ["(l) HTTP.Request"]='\bHTTP\.Request\b'
        ["(m) require_shell recursion"]='pc\s*=\s*require_shell\s*\('
        ["(n) NO //command: marker"]='MISSING_MARKER'
    )
    
    declare -A TOTALS
    declare -A FILE_HITS
    
    # Run patterns
    for label in "${!PATTERNS[@]}"; do
        regex="${PATTERNS[$label]}"
        count=0
        files_hit=""
        
        for f in "${FILES[@]}"; do
            if [[ "$label" == "(n) NO //command: marker" ]]; then
                # Library filter (per skill-references/bug-scan-sweep-2026-07-07.md Pitfall 2)
                if echo "$f" | grep -qiE "lib_core|listlib|util\.src|/core/|recon_lite|tests/test_|cli_core|libcore|buildcore|netcore|debugcore|filecore|cliFeedback|lzw/|xmem|minitest/libs/|minitest/examples/|fix_perms|attack_tiers|ransomeware|install|installer/"; then
                    continue
                fi
                first=$(head -1 "$f" 2>/dev/null)
                if [[ ! "$first" =~ ^//command: ]]; then
                    count=$((count + 1))
                    files_hit+="$f "
                fi
            elif [[ "$label" == "(b) ternary X if C else Y" ]]; then
                # Skip else-if chains
                hits=$(grep -cE "$regex" "$f" 2>/dev/null | head -1)
                if [[ -n "$hits" && "$hits" -gt 0 ]]; then
                    # Refine: count only ternary (no `then` between if and else)
                    refined=$(grep -cE '^[^/]*\bif\b.*\belse\b' "$f" 2>/dev/null | head -1)
                    if [[ -n "$refined" && "$refined" -gt 0 ]]; then
                        # Subtract else-if chains
                        elseif=$(grep -cE '\belse\s+if\b' "$f" 2>/dev/null | head -1)
                        net=$((refined - elseif))
                        if [[ "$net" -gt 0 ]]; then
                            count=$((count + net))
                            files_hit+="$f "
                        fi
                    fi
                fi
            elif [[ "$label" == "(d) single-quote 'text' in CODE" ]]; then
                # Skip if all hits are in print() messages (heuristic)
                hits=$(grep -cE "$regex" "$f" 2>/dev/null | head -1)
                if [[ -n "$hits" && "$hits" -gt 0 ]]; then
                    code_hits=$(grep -E "if\s+\S+\s*[!=]=\s*'" "$f" 2>/dev/null | wc -l)
                    if [[ "$code_hits" -gt 0 ]]; then
                        count=$((count + code_hits))
                        files_hit+="$f "
                    fi
                fi
            elif [[ "$label" == "(f) \\ in strings" ]]; then
                # Skip if char(34) workaround present
                hits=$(grep -cE "$regex" "$f" 2>/dev/null | head -1)
                if [[ -n "$hits" && "$hits" -gt 0 ]]; then
                    without_workaround=$(grep -E '\\"' "$f" | grep -v "char(34)" | grep -v "^//" | wc -l)
                    if [[ "$without_workaround" -gt 0 ]]; then
                        count=$((count + without_workaround))
                        files_hit+="$f "
                    fi
                fi
            else
                hits=$(grep -cE "$regex" "$f" 2>/dev/null | head -1)
                if [[ -n "$hits" && "$hits" -gt 0 ]]; then
                    count=$((count + hits))
                    files_hit+="$f "
                fi
            fi
        done
        
        TOTALS[$label]=$count
        FILE_HITS[$label]="$files_hit"
    done
    
    # Report
    echo ""
    echo "  Pattern | Total"
    echo "  --------|------"
    for label in "(a) one-line-if/then/end if" "(b) ternary X if C else Y" \
                 "(c) \\n statt char(10)" "(d) single-quote 'text' in CODE" \
                 "(e) inline-if assignment" "(f) \\ in strings" \
                 "(g) === separator line" "(h) [^N] negative index" \
                 "(i) .strip()/.trim()" "(j) str_repeat" \
                 "(k) get_system_time" "(l) HTTP.Request" \
                 "(m) require_shell recursion" "(n) NO //command: marker"; do
        printf "  %-50s | %d\n" "$label" "${TOTALS[$label]:-0}"
    done
    
    echo ""
    echo "  Files per pattern (for Sub-Agent-Dispatch):"
    for label in "${!FILE_HITS[@]}"; do
        if [[ -n "${FILE_HITS[$label]// /}" ]]; then
            count=$(echo "${FILE_HITS[$label]}" | wc -w)
            echo "    [$label]: $count files"
            for f in ${FILE_HITS[$label]}; do
                echo "      $f"
            done
        fi
    done
fi

# === STEP 2: Build-Verifikation (5-Kategorien-Klassifizierung) ===
if [[ "$SCAN_ONLY" -eq 0 ]]; then
    echo ""
    echo "=== STEP 2: Build-Verifikation (greybel) ==="
    
    if ! command -v greybel &>/dev/null; then
        echo "  ⚠️  greybel not found. Install with: npm install -g @greybel/greybel-js"
        exit 1
    fi
    
    OUT_DIR=".ci-build-audit-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$OUT_DIR"
    
    declare -A CATEGORIES=(
        ["pattern_bug"]=0
        ["import_resolution"]=0
        ["api_not_found"]=0
        ["type_mismatch"]=0
        ["mock_env_only"]=0
        ["other"]=0
    )
    declare -A CATEGORY_FILES
    
    PASS=0
    FAIL=0
    
    for f in "${FILES[@]}"; do
        target="$OUT_DIR/${f//\//_}"
        mkdir -p "$target"
        err_log="$(mktemp)"
        
        if greybel build "$f" "$target" -dbf 2>"$err_log"; then
            PASS=$((PASS + 1))
        else
            FAIL=$((FAIL + 1))
            err=$(cat "$err_log")
            
            # Categorize
            category="other"
            if echo "$err" | grep -qE "got Keyword|no matching open if block|unexpected token"; then
                category="pattern_bug"
            elif echo "$err" | grep -qE "Dependency.*does not exist"; then
                category="import_resolution"
            elif echo "$err" | grep -qE "undefined function|Path.*not found"; then
                category="api_not_found"
            elif echo "$err" | grep -qE "got Identifier where"; then
                category="type_mismatch"
            elif echo "$err" | grep -qE "Mock Environment|Path.*not found in map"; then
                category="mock_env_only"
            fi
            
            CATEGORIES[$category]=$((CATEGORIES[$category] + 1))
            CATEGORY_FILES[$category]="${CATEGORY_FILES[$category]:-} $f"
        fi
        rm -f "$err_log"
    done
    
    echo ""
    echo "  Build results: $PASS OK / $FAIL FAIL of ${#FILES[@]}"
    echo ""
    echo "  === 5-Kategorien-Klassifizierung (Failures) ==="
    for cat in "pattern_bug" "import_resolution" "api_not_found" "type_mismatch" "mock_env_only" "other"; do
        printf "    %-20s | %d\n" "$cat" "${CATEGORIES[$cat]:-0}"
        if [[ -n "${CATEGORY_FILES[$cat]:-}" ]]; then
            for f in ${CATEGORY_FILES[$cat]}; do
                echo "        $f"
            done
        fi
    done
fi

echo ""
echo "=== DONE ==="