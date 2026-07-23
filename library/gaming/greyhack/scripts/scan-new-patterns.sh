#!/bin/bash
# GreyScript Bug-Pattern Discovery Scan
# Scans all .src files for patterns NOT yet in BUG-PATTERNS.md
# Usage: bash scan-new-patterns.sh [greyhack-tools-dir]

TOOLS_DIR="${1:-$HOME/greyhack-tools}"
REPORT_DIR="$HOME/docs/system"
TIMESTAMP=$(date +%Y-%m-%d-%H-%M)
REPORT_FILE="$REPORT_DIR/greyhack-research-$TIMESTAMP.md"

mkdir -p "$REPORT_DIR"

echo "# GreyHack Bug-Pattern Research Report" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "**Datum:** $TIMESTAMP" >> "$REPORT_FILE"
echo "**Quelle:** Automatisierter Grep-Scan von $TOOLS_DIR" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Build active file list (exclude backups and imports)
ACTIVE_FILES=$(find "$TOOLS_DIR" -name "*.src" -type f | grep -v '/backups/' | grep -v '/de/imports/' | sort)
ACTIVE_COUNT=$(echo "$ACTIVE_FILES" | wc -l)
echo "**Aktive Dateien:** $ACTIVE_COUNT" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "## Scan Results" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Pattern 1: range off-by-one
echo "### 1. range(0, x.len - 1) Off-by-One" >> "$REPORT_FILE"
P1=$(echo "$ACTIVE_FILES" | xargs grep -l 'range.*\.len.*-.*1' 2>/dev/null)
if [ -n "$P1" ]; then
    echo "FOUND in:" >> "$REPORT_FILE"
    echo "$P1" | while read f; do echo "- \`$f\`" >> "$REPORT_FILE"; done
else
    echo "NOT FOUND" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Pattern 2: map.count definition
echo "### 2. map.count definition" >> "$REPORT_FILE"
P2=$(echo "$ACTIVE_FILES" | xargs grep -l 'map\.count.*function' 2>/dev/null)
if [ -n "$P2" ]; then
    echo "FOUND in:" >> "$REPORT_FILE"
    echo "$P2" | while read f; do echo "- \`$f\`" >> "$REPORT_FILE"; done
else
    echo "NOT FOUND" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Pattern 3: applyFunction
echo "### 3. applyFunction" >> "$REPORT_FILE"
P3=$(echo "$ACTIVE_FILES" | xargs grep -l 'applyFunction' 2>/dev/null)
if [ -n "$P3" ]; then
    echo "FOUND in:" >> "$REPORT_FILE"
    echo "$P3" | while read f; do echo "- \`$f\`" >> "$REPORT_FILE"; done
else
    echo "NOT FOUND" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Pattern 4: join char(10) literal
echo "### 4. join(\"char(10)\") literal" >> "$REPORT_FILE"
P4=$(echo "$ACTIVE_FILES" | xargs grep -l 'join.*"char(10)"' 2>/dev/null)
if [ -n "$P4" ]; then
    echo "FOUND in:" >> "$REPORT_FILE"
    echo "$P4" | while read f; do echo "- \`$f\`" >> "$REPORT_FILE"; done
else
    echo "NOT FOUND" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Pattern 5: show_procs split
echo "### 5. show_procs split" >> "$REPORT_FILE"
P5=$(echo "$ACTIVE_FILES" | xargs grep -l 'show_procs.*split' 2>/dev/null)
if [ -n "$P5" ]; then
    echo "FOUND in:" >> "$REPORT_FILE"
    echo "$P5" | while read f; do echo "- \`$f\`" >> "$REPORT_FILE"; done
else
    echo "NOT FOUND" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

echo "Report written to: $REPORT_FILE"
