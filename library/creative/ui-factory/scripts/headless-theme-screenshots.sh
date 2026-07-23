#!/usr/bin/env bash
# ============================================================================
# Headless Theme Screenshot Script (ui-factory)
# ============================================================================
# Purpose: Render every theme of a ui-factory build as a PNG via Google Chrome
#          headless, so the result can be visually validated when no
#          interactive browser tools are available.
# Usage:   ./scripts/headless-theme-screenshots.sh <base-url> <output-dir> [theme-list]
# Example: ./scripts/headless-theme-screenshots.sh http://127.0.0.1:8765 /tmp/shots
#          ./scripts/headless-theme-screenshots.sh http://127.0.0.1:8765 /tmp/shots "light dark cyber hc"
# Notes:   The target HTML must read `?theme=<value>` and apply it before
#          first paint (see ui-factory Pitfall 9 for the JS snippet).
# ============================================================================

set -euo pipefail

BASE_URL="${1:?Usage: $0 <base-url> <output-dir> [theme-list]}"
OUT_DIR="${2:?Usage: $0 <base-url> <output-dir> [theme-list]}"
THEMES="${3:-light dark cyberpunk hc a11y}"
WIDTH="${WIDTH:-1440}"
HEIGHT="${HEIGHT:-1100}"

mkdir -p "$OUT_DIR"

for theme in $THEMES; do
  out="$OUT_DIR/${theme}.png"
  echo "→ $theme → $out"
  google-chrome \
    --headless \
    --disable-gpu \
    --no-sandbox \
    --hide-scrollbars \
    --window-size="${WIDTH},${HEIGHT}" \
    --virtual-time-budget=2000 \
    --screenshot="$out" \
    "${BASE_URL}/index.html?theme=${theme}" \
    2>&1 | tail -1
done

echo ""
echo "✓ Done. Screenshots in $OUT_DIR:"
ls -la "$OUT_DIR"/*.png