# Phase 8: Design Rework (CSS Visual + MOC Structure)

> **Vault visual theming and MOC standardization via Gemini.** After Gemini densifies cross-links (Phase 7), this phase targets the **visual presentation** (CSS snippets, graph.json colorGroups) and **navigation clarity** (MOC standardization, Home-MOC enrichment).
>
> **Proven 2026-07-05:** 9 → 13 CSS-Snippets (+4 neue), 18/18 MOCs standardisiert, graph.json 16 colorGroups (vorher 15, +1 für `#offen`), 1 neuer Satelliten-MOC (`MOC - System-Wartung.md`).

## When to enter Phase 8

| Condition | How to check |
|---|---|
| Phase 7 complete | Cross-links densified, Gemini proven safe |
| CSS snippets ≥ 9 active | `ls .obsidian/snippets/*.css \| wc -l` ≥ 9 |
| `appearance.json` lists all snippets | JSON valid, enabledCssSnippets complete |
| `graph.json` shows black nodes | `rgb: 0` present in colorGroups |
| MOCs exist but not standardized | 11 MOCs, no consistent section structure |
| User says "design rework" | Explicit design-phase go-ahead |

## Cluster A: CSS Visual Expansion

Gemini (via `--yolo`) creates **3-5 new yuno-*.css snippets** and **patches existing ones** additively.

**Approved scope:**
- **New:** `yuno-callout-banners`, `yuno-metadata-banners`, `yuno-code-blocks`, `yuno-checkboxes`, `yuno-quote-blocks`
- **Extended:** `yuno-moc-style.css` (banner variants, hover effects), `yuno-daily-note-style.css` (time-based highlighting), `yuno-wiki-links.css` (internal vs external distinction)
- **graph.json:** Replace all `rgb: 0` with Yuno-Palette colors (14 tag clusters), tune multipliers
- **appearance.json:** Register new snippets via additive patch

## Cluster B: MOC Structure Standardization

- **MOC - Home.md** — new sections appended: Recent Activity, Knowledge Heatmap, Quick-Access, Cross-Cluster-Hot-Paths
- **All 11 MOCs** — standardized section structure (Übersicht, Notes-in-Folder, Verbindet-zu, Sub-Themen)
- **Satellite MOCs** — max 2 new if genuine gap (Pattern 6)

## Anti-Patterns (Phase 8)

1. ❌ Bestehende CSS-Snippets komplett überschreiben (nur additive Patches!)
2. ❌ Yuno-Farbpalette ändern (`yuno-variables.css` bleibt)
3. ❌ Sanctum-Theme komplett overriden
4. ❌ Andere Themes installieren (Sanctum bleibt)
5. ❌ CSS-Snippets löschen
6. ❌ Vault-Notes außer MOCs anfassen
7. ❌ MOC-Home komplett ersetzen (additive Sektionen ans Ende)
8. ❌ Dataview-Queries ohne Hinweis wenn Plugin-Status ungewiss ist (Drift zwischen community-plugins.json und `.obsidian/plugins/<id>/` vermeiden)
9. ❌ appearance.json-Einträge entfernen (nur anhängen)
10. ❌ Verbotene Folder anfassen (01 Kontext, 02 Inbox, 07 Archiv, 08 Anhaenge, _templates, .trash)

## Verifikation (Post-Phase 8)

```bash
# CSS-Snippet-Anzahl (vorher 9, erwartet 12-14)
find "$VAULT/.obsidian/snippets" -name '*.css' | wc -l

# graph.json: no rgb:0
grep -c '"rgb": 0' "$VAULT/.obsidian/graph.json"  # expected: 0

# Neue Snippets > 60 Zeilen
for f in "$VAULT/.obsidian/snippets"/*.css; do echo "$(wc -l < "$f") $f"; done

# appearance.json: valides JSON, alle referenzierten existieren
python3 -c "
import json
with open('$VAULT/.obsidian/appearance.json') as f:
    data = json.load(f)
    enabled = set(data['enabledCssSnippets'])
    existing = {f.replace('.css','') for f in __import__('os').listdir('$VAULT/.obsidian/snippets') if f.endswith('.css')}
    missing = enabled - existing
    print(f'Enabled: {len(enabled)}, Existing: {len(existing)}, Missing: {missing or \"none\"}')
"

# Anti-Pattern-Diff-Check: yuno-variables.css unverändert
md5sum "$VAULT/.obsidian/snippets/yuno-variables.css"
# Verbotene Folder via diff gegen Backup
BACKUP=$(ls -dt $HOME/.cache/vault-backups/phase8-* 2>/dev/null | head -1)
if [ -n "$BACKUP" ]; then
  diff -rq --exclude='_MOC.md' "$BACKUP/07 Archiv/" "$VAULT/07 Archiv/" 2>/dev/null
  diff -rq "$BACKUP/01 Kontext/" "$VAULT/01 Kontext/" 2>/dev/null
  diff -rq "$BACKUP/08 Anhaenge/" "$VAULT/08 Anhaenge/" 2>/dev/null
  diff -rq "$BACKUP/_templates/" "$VAULT/_templates/" 2>/dev/null
fi
# Gemini-Temp-Files (update_mocs.py, etc.)
find "$VAULT" -maxdepth 1 -name '*.py' 2>/dev/null | grep -v '^$' || echo "Keine Temp-Files"
```

## Anti-Pattern-Verstöße als Pitfall

Gemini verletzte **2 von 10 Anti-Pattern-Regeln** trotz expliziter Verbote im Plan:

1. **`07 Archiv/_MOC.md` modifiziert** (Anti-Pattern #10: "Verbotene Folder") — nur additive Änderung am Ende, kein inhaltlicher Schaden.
2. **Temp-File im Vault-Root** (`update_mocs.py`) — Gemini erstellt gelegentlich Hilfsskripte im Arbeitsverzeichnis.

**Lesson:** `_MOC.md`-Files in verbotenen Foldern können von Gemini als `*/_MOC.md`-Match interpretiert werden. Nach jedem Run `find $VAULT -maxdepth 1 -name '*.py'` prüfen und gefundene Dateien löschen.