#!/usr/bin/env bash
# verify_greybel_builds.sh — batch-build N greybel .src files and report pass/fail
#
# Usage: verify_greybel_builds.sh [-o OUTPUT_BASE] [--] <file.src> [<file.src> ...]
#
# -o OUTPUT_BASE  Output directory for build artifacts (default: /tmp/verify-greybel-builds)
#                 Each file gets a subdirectory named after the file's basename.
# --              End of options marker
#
# Exit codes:
#   0  All builds succeeded
#   1  At least one build failed
#   2  Usage error (no files given / bad args)
#
# Requires: greybel (npm install -g greybel-js), bash 4+

set -euo pipefail

OUTPUT_BASE="/tmp/verify-greybel-builds"

# Parse args
files=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o)
      OUTPUT_BASE="$2"
      shift 2
      ;;
    --)
      shift
      while [[ $# -gt 0 ]]; do
        files+=("$1")
        shift
      done
      ;;
    -*)
      echo "Unknown flag: $1" >&2
      exit 2
      ;;
    *)
      files+=("$1")
      shift
      ;;
  esac
done

if [[ ${#files[@]} -eq 0 ]]; then
  echo "Usage: $0 [-o OUTPUT_BASE] [--] <file.src> [<file.src> ...]" >&2
  exit 2
fi

if ! command -v greybel >/dev/null 2>&1; then
  echo "greybel not found in PATH. Install: npm install -g greybel-js" >&2
  exit 2
fi

mkdir -p "$OUTPUT_BASE"

PASS=0
FAIL=0
FAILED_FILES=()

for src in "${files[@]}"; do
  if [[ ! -f "$src" ]]; then
    echo "❌ MISSING: $src"
    FAIL=$((FAIL + 1))
    FAILED_FILES+=("$src (file not found)")
    continue
  fi

  basename_src=$(basename "$src" .src)
  out_dir="$OUTPUT_BASE/$basename_src/build"

  # capture stderr+stdout; ignore exit-code failure in pipeline so we can grep
  output=$(greybel build "$src" "$out_dir" -dbf -si 2>&1) || true

  if [[ -z "$output" ]]; then
    echo "✅ $src"
    PASS=$((PASS + 1))
  else
    echo "❌ $src"
    # Show first 3 lines of the error
    echo "$output" | head -3 | sed 's/^/   /'
    FAIL=$((FAIL + 1))
    FAILED_FILES+=("$src")
  fi
done

echo ""
echo "===== SUMMARY: $PASS pass / $FAIL fail ====="
if [[ $FAIL -gt 0 ]]; then
  echo "Failed:"
  for f in "${FAILED_FILES[@]}"; do
    echo "  - $f"
  done
  exit 1
fi
exit 0
