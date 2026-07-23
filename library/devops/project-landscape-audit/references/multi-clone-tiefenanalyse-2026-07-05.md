# Multi-Clone Tiefenanalyse — 4 Hermes V7 Clones (gleicher Remote)

> **Referenz-Beispiel** für Phase 4E (Clone Depth Analysis) der `project-landscape-audit` Methodik.
> Scanning von 4 Git-Clones, die alle auf `https://github.com/Toqsick/hermes-v7.git` zeigen.
> **Scan-Datum:** 2026-07-05

## Ausgangslage

| # | Pfad | Branch | Stand | Anomalie |
|---|------|--------|-------|----------|
| 1 | `30-Library/hermes-v7/` | `feat/security-kernel` | Aktiv | ⚠ untracked `logs/audit.jsonl` |
| 2 | `10-Projekte/20-experimental/hermes-v7-wt/` | `feature/yuno-mobil-setup-bundle` | Aktiv | ✅ |
| 3 | `10-Projekte/20-experimental/hermes-v7-orphan/` | `main` (lokal alt) | Veraltet | 🚨 **Token-Leak** |
| 4 | `10-Projekte/40-archive/hermes-zorin/` | `Zorin-Hermes-alt` (archive) | Historisch | ✅ |

## Depth Analysis Commands

### 1. Branch Divergence (vs remote main)

```bash
# Für jeden Clone:
git fetch origin main --depth=1
git rev-list --left-right --count origin/main...HEAD    # → "ahead behind"
git log --oneline origin/main..HEAD                      # → unique commits
git diff --name-only origin/main..HEAD                   # → changed files
git log -1 --format='%ci %s'                             # → last commit
```

**Ergebnis C1:** `0 ahead, 1 behind` — 1 unique Commit (`f704ff1 feat(security): SecurityKernel`)
**Ergebnis C2:** `0 ahead, 1 behind` — 1 unique Commit (`207560f feat(yuno-mobil): MaxClaw-style setup bundle`)
**Ergebnis C4:** `1 ahead, 10 behind` — 9 unique Commits + eigenständige Branch-Geschichte

### 2. File-Level Diff

```bash
git diff --name-only origin/main..HEAD
```

**C1 vs main:** `package-lock.json`, `package.json`, `src/roles/__tests__/orchestrator.test.ts`, `src/roles/orchestrator.ts`, `src/security/__tests__/kernel.test.ts`, `src/security/index.ts`, `src/security/kernel.ts`, `src/security/tool-profiles.ts` — **8 Files, Security-Fokus**

**C2 vs main:** `docs/NAVIGATION.md`, `setup-guide/yuno-mobil-setup/*` (8 Files) — **9 Files, Doku/Build-Fokus**

**C4 vs main:** 100+ Files — komplette hub-imported `skills/` Bibliothek (21 Skills), ADRs (`docs/adr/`), Depp-Layer (`src/depp/`), Storage (`src/storage/`), Runtime, Dashboard, CI — **eigenständiger Snapshot**

### 3. Credential & Hygiene Audit

```bash
# Token-Check
URL=$(git -C "$CLONE" config --get remote.origin.url)
echo "$URL" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p'  # Extrahiert Token

# .git/config Permissions
stat -c '%a' "$CLONE/.git/config"                         # Sollte 600 oder 640

# Credential Helper
git -C "$CLONE" config --get credential.helper             # Sollte libsecret/store/cache

# Untracked Files
git -C "$CLONE" ls-files --others --exclude-standard       # Dirty Files
```

**Befund Clone 3:**
- Token `gho_2X...Lz1g` (40 Zeichen, Klartext in git URL)
- `.git/config` Mode **664** (group-readable!)
- Kein `credential.helper` gesetzt
- → **P0 Security Issue — Token sofort revoken und URL sanitisieren**

**Befund Clone 1:**
- `logs/audit.jsonl` untracked, nicht in `.gitignore`
- → `.gitignore` um `logs/*.jsonl` ergänzen

### 4. CI & Test Coverage

```bash
ls .github/workflows/                              # Existiert CI?
cat .github/workflows/ci.yml | head -20            # CI-Konfiguration
find src/ -name '*.test.*' | wc -l                 # Anzahl Tests
ls src/                                             # Module vorhanden?
```

**C1:** 11 Test-Files (`kernel.test.ts` nur hier!), 10 `src/`-Verzeichnisse, CI auf main/develop
**C2:** 9 Test-Files, 10 `src/`-Verzeichnisse, CI auf main/develop
**C4:** 0 Test-Files, 8 `src/`-Verzeichnisse, **keine Tests**

## Konsolidierungsempfehlung

| Schritt | Aktion | Warum |
|---------|--------|-------|
| 🔴 Sofort | Token auf GitHub revoken, URL sanitisieren | Token-Leak in Clone 3 |
| 🔴 Sofort | `logs/audit.jsonl` in `.gitignore` eintragen | Verhindert Secret-Commit |
| 📋 Phase 2 | C1 als Working-Copy, C2+CI-Tests für Yuno-Mobil-Bundle | C1 hat SecurityKernel + Tests |
| 📋 Phase 2 | C4 als Archiv-Referenz behalten (nicht pushen) | Einzige Quelle für ADRs + Depp-Layer |
| 🗑️ Cleanup | C3 nach Token-Revoke + Quarantäne löschen | Nur noch Risiko, keine exklusiven Inhalte |

## Gelerntes (für künftige Audits)

1. **Immer `git rev-list --left-right --count origin/main...HEAD`** — die pure `git status` sagt nichts über Divergenz.
2. **`git diff --name-only` ist der beste "Was ist anders"-Checker** — zeigt genau welche Files im Feature-Branch liegen.
3. **`.git/config` Mode checken!** `664` ist ein sofortiges Rotlicht.
4. **Token in Remote URL** ist das häufigste Credential-Leak-Pattern — immer auf `gho_*`, `ghp_*`, `github_pat_*` scannen.
5. **0 Test-Files in einem Clone ≠ "kaputt"** — kann Archiv sein. Dokumentieren, nicht löschen.
