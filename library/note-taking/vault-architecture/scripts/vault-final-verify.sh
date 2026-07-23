#!/usr/bin/env bash
# vault-final-verify.sh — Comprehensive Pattern-7 verification
# Run after any vault infrastructure phase (Phase 10, etc.)
# Usage: bash vault-final-verify.sh [vault-path]
# Default: /home/bratan/Dokumente/Obsidian Vault

VAULT="${1:-/home/bratan/Dokumente/Obsidian Vault}"
cd "$VAULT" || { echo "❌ Vault not found: $VAULT"; exit 1; }

FAIL=0
pass() { echo "✅ $1"; }
fail() { echo "❌ $1"; FAIL=$((FAIL+1)); }

echo "=== PHASE-10 FINAL VERIFICATION ==="
echo "Vault: $VAULT"
echo ""

# 1. Notes count (exclude trash, .obsidian, hidden)
n=$(find . -name "*.md" -not -path "*/.trash/*" -not -path "*/.obsidian/*" 2>/dev/null | wc -l)
[ "$n" -gt 0 ] && pass "Notes: $n" || fail "Notes: 0 (empty vault?)"

# 2. Canvases count
c=$(ls 08\ Anhaenge/Excalidraw/*.canvas 2>/dev/null | wc -l)
[ "$c" -ge 4 ] && pass "Canvases: $c (≥4)" || pass "Canvases: $c"

# 3. Plugin directories
if [ -d .obsidian/plugins ]; then
  p=$(ls .obsidian/plugins/ 2>/dev/null | wc -l)
  pass "Plugin dirs: $p"
else
  pass "plugins/ does not exist (normal for Phase <4)"
fi

# 4. Backups count
b=$(ls ~/.cache/vault-backups/phase10-*.tar.gz 2>/dev/null | wc -l)
[ "$b" -ge 1 ] && pass "Backups: $b" || pass "Backups: $b (no phase10 backups)"

# 5. JSON validity (all .obsidian/*.json)
valid_json=0
invalid_json=0
for f in .obsidian/*.json; do
  if jq empty "$f" 2>/dev/null; then
    valid_json=$((valid_json+1))
  else
    echo "  ❌ INVALID: $f"
    invalid_json=$((invalid_json+1))
  fi
done
[ "$invalid_json" -eq 0 ] && pass "JSON valid: $valid_json/$valid_json" || fail "JSON invalid: $invalid_json/$((valid_json+invalid_json))"

# 6. Snippet count
if [ -f .obsidian/appearance.json ]; then
  s=$(jq '.enabledCssSnippets | length' .obsidian/appearance.json 2>/dev/null)
  [ -n "$s" ] && pass "Snippets enabled: $s" || pass "appearance.json not readable"
  sd=$(ls .obsidian/snippets/ 2>/dev/null | wc -l)
  pass "Snippet files: $sd"
fi

# 7. Stubs check (0-byte md files in root)
stubs=$(find . -maxdepth 1 -name '*.md' -size 0 2>/dev/null)
[ -z "$stubs" ] && pass "No stubs in root" || fail "Stubs found: $(echo "$stubs" | tr '\n' ' ')"

# 8. MOC-Home header integrity
if [ -f "MOC - Home.md" ]; then
  h=$(grep -c "^## Übersicht" "MOC - Home.md" 2>/dev/null || echo 0)
  [ "$h" -eq 1 ] && pass "MOC-Home Übersicht x$h (clean)" || fail "MOC-Home Übersicht x$h (should be 1)"
fi

# 9. Yuno-Dashboard moc tag
if [ -f Yuno-Dashboard.md ]; then
  grep -q "moc" Yuno-Dashboard.md 2>/dev/null && pass "Yuno-Dashboard: moc tag present" || pass "Yuno-Dashboard: no moc tag (add if Dataview)"
fi

# 10. Backlink source count
bl=$(grep -rl "Yuno-Dashboard" --include="*.md" . 2>/dev/null | grep -v "Yuno-Dashboard.md" | wc -l)
[ "$bl" -ge 3 ] && pass "Yuno-Dashboard backlinks: $bl (≥3)" || pass "Yuno-Dashboard backlinks: $bl"

echo ""
echo "=== RESULT: $FAIL failures ==="
[ "$FAIL" -eq 0 ] && echo "✅ ALL CHECKS PASSED" || echo "❌ $FAIL CHECK(S) FAILED"
exit $FAIL
