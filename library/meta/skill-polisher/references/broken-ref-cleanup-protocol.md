# Broken-Ref Cleanup Protocol

> **Stand:** 2026-07-16  
> **Kategorisiert von:** Biene P2 (Broken-Ref-Tagger)  
> **Live-Count:** 283 real broken refs über 96 Skills

---

## Kategorien

| Code | Kategorie | Count | Definition |
|---|---|---|---|
| `B` | BUNDLE_MISSING | 151 | Skill hat kein `references/` oder `scripts/` Dir, aber SKILL.md referenziert Pfade darin |
| `F` | FILE_MISSING | 110 | Dir existiert, aber die konkrete referenzierte Datei fehlt |
| `T` | TEMPLATE_PLACEHOLDER | 4 | Ref enthält `example`, `<name>`, `DATE` — generischer Platzhalter |

## Top-20 Skills mit meisten Broken Refs (2026-07-16)

```
Count  [B/F/T]   Skill-Pfad
  18    [1/17/0]   creative/creative-suite
  15    [15/0/0]   creative/manim-video
  12    [3/9/0]    productivity/daily-briefing
  11    [9/0/2]    creative/html-artifact
  11    [0/11/0]   voice-assistant-bots
   9    [2/7/0]    software-development/skill-format-conversion
   8    [8/0/0]    creative/ascii-video
   7    [7/0/0]    software-development/the-dmz-transfer
   6    [3/3/0]    orchestration/pitfalls
   5    [0/5/0]    note-taking/system-documentation
   5    [1/4/0]    devops/hermes-admin (1× Tippfehler scripts/scripts/)
   5    [5/0/0]    devops/host-security-audit
   5    [0/5/0]    devops/security-audit
   4    [4/0/0]    software-development/bash-script-audit
   4    [4/0/0]    productivity/epub-export
   4    [3/0/1]    creative/excalidraw
   4    [4/0/0]    creative/pixel-art
   4    [0/4/0]    third-party-bundle-patch-release
   4    [0/4/0]    devops/hermes-maintenance
   3    [1/2/0]    orchestration/multi-agent-cluster-patterns
```

## P0/P1/P2 Empfehlung

### P0 — Sofort fixen
1. **Bundle-Hot-Spots (9 Skills, ~60 BUNDLE_MISSING):** `mkdir -p <skill>/references <skill>/scripts && touch <skill>/references/.gitkeep <skill>/scripts/.gitkeep`
   - creative/manim-video (15), creative/ascii-video (8), creative/html-artifact (9)
   - software-development/the-dmz-transfer (7), devops/host-security-audit (4)
   - software-development/bash-script-audit (4), productivity/epub-export (3)
   - creative/excalidraw (3), creative/pixel-art (3)
2. **Tippfehler patchen:** `devops/hermes-admin: scripts/scripts/` → `scripts/`
3. **voice-assistant-bots (11 FILE_MISSING):** Stubs erstellen oder Refs entfernen

### P1 — Nächste Welle
- **creative-suite (17 FILE_MISSING):** Hub-Skill, Sub-Skills extern verlinkt. Verifizieren ob relative Pfade oder Cross-Skill-Links.
- **daily-briefing (12 broken):** Historische Refs auf migrierte Workflows. Sichten.
- **security-audit (5) + system-documentation (5) + skill-format-conversion (9):** Produktive Method-Skills, Einzelfall-Entscheidung.

### P2 — Opportunistisch
- **TEMPLATE_PLACEHOLDER (4):** Entweder echte Beispiele erstellen oder Ref streichen.
- **54 Bundle-Skills unter 3 Broken Refs:** Bulk-Cleanup-Script.
- **29 Skills mit FILE_MISSING only (60 Refs):** Einzelfall-Entscheidung.

## Scanner-Script (für Queen-Verify)

```bash
python3 -c "
import os, re, glob
home = os.path.expanduser('~')
broken = []
for f in glob.glob(f'{home}/.hermes/skills/**/SKILL.md', recursive=True):
    if '.archive/' in f or '.curator_backups/' in f: continue
    d = os.path.dirname(f)
    with open(f) as fh:
        refs = re.findall(r'(?:references|scripts|assets|templates)/[\w./-]+', fh.read())
    for r in set(refs):
        rp = os.path.join(d, r)
        if not os.path.exists(rp) and not os.path.exists(r):
            if not re.search(r'(<|>|{|}|foo|bar|example|DATE)', r):
                broken.append((
                    f.replace(home, '~'),
                    r,
                    'BUNDLE' if not os.path.exists(os.path.join(d, r.split('/')[0])) else 'FILE'
                ))
# Summarize
by_cat = {'BUNDLE': 0, 'FILE': 0}
for _, _, cat in broken: by_cat[cat] += 1
print(f'Total: {len(broken)} (BUNDLE={by_cat[\"BUNDLE\"]}, FILE={by_cat[\"FILE\"]})')
# Top-10 by skill
from collections import Counter
top = Counter(f for f,_,_ in broken).most_common(10)
for skill, count in top: print(f'  {skill}: {count}')
"
```

## Bulk-Skript: Alle Bundle-Dirs anlegen

```bash
#!/bin/bash
# Run from ~/.hermes/skills/
for skill in \
  "creative/manim-video" \
  "creative/ascii-video" \
  "creative/html-artifact" \
  "software-development/the-dmz-transfer" \
  "devops/host-security-audit" \
  "software-development/bash-script-audit" \
  "productivity/epub-export" \
  "creative/excalidraw" \
  "creative/pixel-art"
do
  mkdir -p "$skill/references" "$skill/scripts"
  touch "$skill/references/.gitkeep" "$skill/scripts/.gitkeep"
  echo "✅ Created dirs: $skill/"
done
```
