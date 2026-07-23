# GreyHack Tools Audit — 2026-07-05

**Target:** `/home/bratan/10-Projekte/10-active/greyhack-tools/`
**Output document:** `/home/bratan/docs/system/schwarm-refactor-2026-07-05/task-4-dir-structure.md`
**Ceiling:** 800 words

## Findings

### Volume
- 16 Top-Level-Dirs, ~913 Files, 427 MB
- Largest dir: `src/` (196 K, 17 files, 4,795 LOC GreyScript/Python)
- Empty dirs: `xmem/`, `includes/` (nur `.node-persist/storage`, `.gitkeep`)
- Stale: `docs/doku/build/` (leer + mode 750)

### Triple-Snapshot
`greyhack-tools-20260613T144257Z/` exists in **3 locations**:
1. Working tree (`greyhack-tools/`)
2. `imports/` (duplicate)
3. `de/imports/` (triplicate)

Snapshot is 22 days old, working tree has diverged (newer `bltings.src` NP-29, `bootstrap.src` v1.1; missing `parse-exploit-reqs/`, `progress-bar/`, `NAVIGATION.md`).

### Import Patterns (3 types found)
| Pattern | Example | Count | Type |
|---------|---------|-------|------|
| Qualified prefix | `import_code('src/core/libcore.src')` | ~15 | B) Structure-dependent |
| Relative path | `import_code('../tools/portscan.src')` | ~8 | A) File-location-dependent |
| Filename only | `import_code('viper_core.src')` | ~6 | C) Namespace-resolution |

### Key Redundancies
- `tools/portscan.src` (alt) parallel zu `src/tools/portmon.src` — semantisches Duplikat
- `yuno_viper/` (5 files, 3,338 LOC) — semantisch identisch zu `src/` Suite, aber nicht integriert
- `lib_core/` (gamescripts/) ↔ `libcore.src` (src/) — same logic, different names/format

## Proposed Layout (Single-Package)

```
greyhack-tools/
├── src/
│   ├── core/libcore.src, bootstrap.src
│   ├── crypto/crypto.src
│   ├── security/security.src
│   ├── tools/portscan.src, setup.src, tcp.src
│   └── viper/viper_{core,net,post,scan,util}.src
├── gamescripts/
│   └── lib_core/ → symlink src/core/libcore.src (nach Dedup)
├── tests/src/*.src, tests/python/*.py
├── scripts/, tools/, docs/, reports/, .github/, .hermes/, build/, bin/
└── DELETE: imports/, de/, backups/, xmem/, includes/, docs/doku/
```

## Migration Plan (6 phases)

1. **Vorbereitung:** Baseline `pytest -q tests/`, `grep`-Audit aller `import_code(...)` → MIGRATION-MAP.md
2. **In-place Moves:** 5 kleine PRs (gamescripts/→src/, yuno_viper/→src/, tools/→src/, lib_core↔libcore dedup, imports/ cleanup)
3. **Import-Fixes:** Nach jedem Move: grep-Audit → Pfadanpassung → Build-Test
4. **Verifikation:** `pytest -q` Baseline, `bash scripts/ci-build.sh` rebuild, Sandbox-Smoke-Test
5. **Sync:** PR → `develop`, Clone A `git fetch + merge --no-ff`, Tag setzen
6. **Cleanup:** Leere Dirs, falsche Endungen, .gitignore-Anpassungen

## Risk Matrix (top 5)
| Risiko | Impact | Mitigation |
|--------|--------|------------|
| Snapshot-Divergenz | Data loss beim Löschen | Diff before delete, Git recovery |
| Import-Resolvability | Build broken | MIGRATION-MAP.md vor jedem Move |
| Greybel-Rebuild | CI-Build mismatch | Build test after every commit |
| yuno_viper orphan | Code rot im alten Pfad | Zügig integrieren |
| lib_core↔libcore dedup | Doppelte Wartung | Single-Source + Symlink |

## Key Lessons for Future Audits
- File count + LOC per dir geben bessere Priorisierung als du -sh allein
- Dreifach-Snapshots sind schwer zu übersehen — immer alle imports/-Pfade checken
- Migrations-Plan in Phasen statt Mega-PR reduziert Risiko massiv
- 800-Wörter-Limit: Bericht von Anfang an kompakt bauen, nicht iterativ runtertrimmen
