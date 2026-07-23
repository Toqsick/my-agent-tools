#!/usr/bin/env bash
# verify-sub-sub.sh — parent-side proof that a sub-sub dispatch succeeded.
#
# Usage:
#   verify-sub-sub.sh <prefix> <timestamp> [expected_count]
#
# Exits 0 if every check passes, 1 otherwise. Prints a green/red summary
# suitable for piping into the parent Self-Report.
#
# Checks performed:
#   1. ls /tmp/<prefix>/<ts>*  — count of side-effect files matches expected
#   2. For each <ts>-sub.txt line, sha256sum recompute matches the line

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <prefix> <timestamp> [expected_count]" >&2
  exit 2
fi

PREFIX="$1"
TS="$2"
EXPECTED="${3:-2}"   # default to 2 = 1 parent deliverable + 1 sub deliverable

DIR="/tmp/${PREFIX}"
fail=0

echo "=== verify-sub-sub: prefix=${PREFIX} ts=${TS} expected=${EXPECTED} ==="

# Check 1: file count
files=$(ls "${DIR}/${TS}"* 2>/dev/null | wc -l)
if [ "${files}" -eq "${EXPECTED}" ]; then
  echo "  CHECK 1 PASS: ${files} side-effect files match expected=${EXPECTED}"
else
  echo "  CHECK 1 FAIL: found ${files} files, expected ${EXPECTED}"
  ls -la "${DIR}/${TS}"* 2>/dev/null || true
  fail=1
fi

# Check 2: hash recompute (only if a <ts>-sub.txt exists)
hash_file="${DIR}/${TS}-sub.txt"
if [ -f "${hash_file}" ]; then
  echo "  CHECK 2: recomputing hashes from ${hash_file}"
  mismatch=0
  total=0
  while read -r h f; do
    [ -z "${h}" ] && continue
    total=$((total + 1))
    fresh=$(sha256sum "${f}" 2>/dev/null | awk '{print $1}' || echo "ERR")
    if [ "${h}" = "${fresh}" ]; then
      echo "    MATCH: ${f}"
    else
      echo "    MISMATCH: ${f} (sub=${h} fresh=${fresh})"
      mismatch=$((mismatch + 1))
    fi
  done < "${hash_file}"
  if [ "${mismatch}" -eq 0 ] && [ "${total}" -gt 0 ]; then
    echo "  CHECK 2 PASS: ${total}/${total} hashes verified"
  else
    echo "  CHECK 2 FAIL: ${mismatch} of ${total} hashes mismatched"
    fail=1
  fi
else
  echo "  CHECK 2 SKIP: no ${hash_file} found"
fi

if [ "${fail}" -eq 0 ]; then
  echo "=== verify-sub-sub: PASS ==="
  exit 0
else
  echo "=== verify-sub-sub: FAIL ==="
  exit 1
fi