# Comprehensive Final Verification (Phase-10-Pattern)

## When to Run

After any vault infrastructure phase that adds/modifies:
- Community plugins (Dataview, Style Settings, Calendar)
- graph.json colorGroups
- Canvases (08 Anhaenge/Excalidraw/)
- Yuno-Dashboard
- CHANGELOG
- MOC-Home sections

## Verification Script (Single Terminal Call)

```bash
VAULT="/home/bratan/Dokumente/Obsidian Vault"
cd "$VAULT"

# 1. Notes count (md files, excluding trash/.obsidian)
echo "=== Notes ==="
find . -name "*.md" -not -path "*/.trash/*" -not -path "*/.obsidian/*" | wc -l

# 2. Canvases
echo "=== Canvases ==="
ls 08\ Anhaenge/Excalidraw/*.canvas 2>&1

# 3. Plugin dirs
echo "=== Plugins ==="
ls .obsidian/plugins/ 2>&1

# 4. Backups
echo "=== Backups ==="
ls ~/.cache/vault-backups/phase10-*.tar.gz 2>&1
ls ~/.cache/vault-backups/phase10-quarantaene/.obsidian.backup-* 2>&1

# 5. JSON validity
echo "=== JSON Validity ==="
for f in .obsidian/*.json; do
  jq empty "$f" 2>/dev/null && echo "✓ $f"
done

# 6. Snippet count (should be 14 after Phase 10)
echo "=== Snippets ==="
jq '.enabledCssSnippets | length' .obsidian/appearance.json
ls .obsidian/snippets/ | wc -l

# 7. Stubs (should be 0)
echo "=== Stubs ==="
find . -maxdepth 1 -name "*.md" -size 0 2>&1 || echo "✓ keine Stubs"

# 8. MOC-Home integrity
echo "=== MOC-Home ==="
grep -c "^## Übersicht" "MOC - Home.md"  # should be 1

# 9. Yuno-Dashboard frontmatter
echo "=== Yuno-Dashboard ==="
grep -A2 "tags:" Yuno-Dashboard.md | head -5

# 10. Backlink sources
echo "=== Yuno-Dashboard Backlinks ==="
grep -c "Yuno-Dashboard" --include="*.md" -r . 2>/dev/null | grep -v ":0"
```

## Proven Results (Phase 10, 2026-07-05)

| Check | Result |
|---|---|
| Notes | 124 |
| Canvases | 4 (Multi-Agent, Yuno-Beziehung, Hardware-ERAZER, Cron-Infrastruktur) |
| Plugin Dirs | 4 (dataview, obsidian-style-settings, calendar, obsidian-excalidraw-plugin) |
| Backups | 4 phase10-*.tar.gz |
| JSON Validity | 6/6 ✓ |
| Snippets Enabled | 14 |
| Snippet Files | 14 |
| Stubs in Root | 0 |
| MOC-Home Übersicht | 1x (clean) |
| Yuno-Dashboard moc tag | Present |
| Backlink Sources | 14 |
