# Starter-Kit Tool Pipeline

**Workflow:** Ein Repository (Toqsick/greyscripts oder Ähnliches) → game-ready Starter-Kit mit `//command:` + Build-Verify + Deploy + Doku + Commit.

## Trigger

- „Bau die besten Tools + Setup für den Start"
- „Mach Start-Setup für GreyHack"
- „Tool-Stack fuer neues Set bereitmachen"
- „Baue Standalone-Tools aus dem Repo"

## Overview (8 Phasen)

| Phase | Was | Dauer | Output |
|-------|-----|-------|--------|
| 0 | Repo-Status + Deploy-Script + Game-Tools inventarisieren | 60s | Ist-Zustand: was deployed, was fehlt |
| 1 | Tools identifizieren: standalone-faehig, aktiv/beste | 30s | Liste der zu bauenden Tools |
| 2 | `//command:` Zeile 1 setzen auf ALLE aktiven Tools | 60s | Kein Tool ohne Command-Header |
| 3 | greybel build + execute smoke-test | 90s | Build-Status pro Tool |
| 4 | Game-Directory sync (yuno-tools/) | 15s | Alle .src in /mnt/DATA/.../Grey Hack/yuno-tools/ |
| 5 | Deploy-Script-Update (yuno-deploy.sh) | 45s | Deploy-Liste + Build-Check erweitert |
| 6 | Vault-Dokumentation (Obsidian) | 120s | Note: GreyHack-Starter-Kit-YYYY-MM-DD.md |
| 7 | Feature-Branch + Commit (nicht auf main!) | 30s | commit auf `feature/starter-kit-YYYY-MM-DD` |

## Detail-Phasen

### Phase 0 — Inventur

```bash
cd ~/10-Projekte/10-active/greyhack-tools
git status -sb
git branch -a | grep feature
cat "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/yuno-deploy.sh" | grep -A999 'TOOLS=(' | grep -B1 '^)'
ls -la "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/yuno-tools/" | head -30
ss -tlnp | grep 8765
```

### Phase 1 — Tool-Auswahl

| Modus | Beschreibung |
|-------|-------------|
| **Standalone** | Kein `import_code` → direkt paste+run |
| **Core-backed** | Braucht `import_code("bin/libcore")` → `setup` vorher |
| **Flagship** | `yuno_v6` — monolithisch, uglified Build |

Faustregel: Starter-Kit = 2-3 Standalone + bestehende Flagships. Core-backed Tools erst in Stage 2.

### Phase 2 — `//command:` setzen

Jede `.src`-Datei im Deploy-Script muss `//command: <name>` als erste Zeile haben. Fix:

```bash
{ echo "//command: toolname"; cat tool.src; } > tool.src.tmp && mv tool.src.tmp tool.src
```

Auch Library-Module (core/*.src) bekommen `//command:` — macht sie standalone testbar.

### Phase 3 — Build-Verify

```bash
OUT=/tmp/gh-starter-build; mkdir -p "$OUT"
for f in tools/*.src; do echo "=== $(basename $f) ==="; greybel build "$f" "$OUT" -dbf 2>&1 | tail -5; done
for f in tools/*.src; do greybel execute "$f" -p -h --silent 2>&1 | head -10; done
```

**Pitfalls:**
- `char(92)` (backslash) in print-Strings → `Invalid character 92`. Keine Escape-Sequenzen in Strings, `char(10)` fuer newline.
- `//`-Kommentare innerhalb von `{}` Map-Literalen → Fehler. Kommentare auserhalb.
- `import_code` nur wenn core modulbaum vorhanden. Standalone Tools ohne import_code.

### Phase 4-6 — Deploy, Script-Update, Vault-Doku

**Sync:**
```bash
cp tools/<neue>.src "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/yuno-tools/"
```

**Deploy-Script:** Jedes neue Tool in die `TOOLS=(`-Liste von `yuno-deploy.sh` einfuegen. Pruefen: `bash yuno-deploy.sh` muss alle als ✅ zeigen.

**Vault-Note:** `09 System-Doku/GreyHack/GreyHack-Starter-Kit-YYYY-MM-DD.md` mit Repo, Tool-Liste, Deploy-URLs, In-Game Chain, Regeln, Verify-Ergebnissen, Links zu verwandten Notes.

### Phase 7 — Commit

```bash
cd ~/10-Projekte/10-active/greyhack-tools
git checkout -b feature/starter-kit-$(date +%Y-%m-%d) origin/develop
git add tools/<neue-tools>.src src/core/<gepatchte-cores>.src
git commit -m "feat(starter): bootstrap toolkit for GreyHack start setup"
# Nicht pushen ohne User-Freigabe!
```

Niemals direkt auf `main`. Immer von `origin/develop` abzweigen.

## Deploy-URLs (Fileserver :8765)

```
http://192.168.178.92:8765/<tool>.src
```

**In-Game Flow:** Host `bash yuno-deploy.sh` → Browser URL → Copy → CodeEditor Paste → Save als `/home/<USER>/Config/<tool>.src` → Build → Run.

## Regeln (V0.9.x verified 2026-07-14)

- Source in `/home/<USER>/Config/<name>.src`
- `//command:` PFLICHT fuer Deploy-Script + DB-Injection (optional fuer CodeEditor)
- Kein `wget`/`curl` im Terminal — nur `pc.wget()` in GreyScript
- greybel execute mit `--silent` fuer Mock-Tests
- Backup-Pattern: `*.src.bak-YYYYMMDD` vor `//command:`-Patches

## Real-World Data (2026-07-14)

- 12 Tools in Deploy-Liste, alle mit `//command:`
- 5 Starter-Tools neu (yuno_bootstrap, yuno_nscan, yuno_localrecon, setup, portscan)
- 5 Core-Module gepatcht (libcore, cliFeedback, buildcore, netcore, filecore)
- greybel build: 10/10 PASS, execute 3/3 PASS
- Feature-Branch: `feature/starter-kit-2026-07-14` — 1 Commit