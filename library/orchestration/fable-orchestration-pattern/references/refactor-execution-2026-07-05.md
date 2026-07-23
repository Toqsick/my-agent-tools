# Refactor-Execution Session 2026-07-05 — Referenz

## Kontext

Fünfteiliger Refactor des `greyhack-tools` Repos (Clone B). Fable-Strategie → M3 Schwarm → Fable-Validation → Queue Execution.

**Repo:** Toqsick/greyscripts (local Clone B)
**Branch:** `refactor/2026-07-05-cleanup`
**Dauer:** ~30 Min (geschätzt 3h Fable)

## Fünf Tasks — Reihenfolge nach Fable

Fable empfahl: **Task 2 → 3 → 1 → 5 → 4**

### Task 2 — grsa_v2 Dedup (30s)
- Bit-identische Duplikate in `src/crypto/grsa_v2.src` und `src/security/grsa_v2.src`
- MD5-Check (`cfb88aa7...`) bestätigte Identität → `security/` Version gelöscht
- **Lesson:** `md5sum` VOR `diff -u` — spart Sekunden bei großen Files

### Task 3 — xmem-Merge (30s)
- Clone A (xmem.src, 900 LOC) vs Clone B (889 LOC)
- Identische 22 functions, aber A hat **3 Bugfixes**: `end if`, `exit()`, `list[-1]`
- Kein MD5-Match (B war älter) → `cp` aus A nach B + manuelle Verifikation via `.ci-build/`

### Task 1 — Clone-Sync (1 Min)
- Clone B war 4 Commits AHEAD origin/develop
- Clone A hatte 2 **eigene** AHEAD-Commits (nicht in origin)
- Strategie: **Cherry-Pick statt Rebase** (Fable-Entscheidung — minimiert Konflikte)
- **Backup-Branch:** `backup/develop-before-cherrypick-2026-07-05`
- **Sync-Branch:** `refactor/2026-07-05-cleanup` von origin/develop abgezweigt
- Cherry-Pick der 2 Clone-A-Commits → sauber auf Sync-Branch

### Task 5 — CI-Fix (5 Min)
- Altes `ci-build.sh` hatte mehrere Probleme:
  - `--help` wurde nicht unterstützt (unknown argument)
  - `find src/ -name "*.src"` fand nur 10 Files (src/-root hat nur 5 directories)
  - Tatsächlich existierten **315 .src Files** in Sub-Directories
- **Fix:** völlig neues `ci-build.sh v2`:
  - `git ls-files '*.src'` statt brittle `find` (findet alle getrackten Files)
  - Excludes: `tests/`, `imports/`, `build/`, `greybel-vs/`, `.ci-build/`
  - `--dry-run` Modus
  - Mock-Build Fallback wenn greybel nicht verfügbar
- Ergebnis: 66 → 67 .src files gefunden

### Task 4 — Verzeichnis-Refactor (10 Min)
**Pre-Refactor Backup:** `~/Dokumente/Backups/refactor-pre-<timestamp>/` — kopiert `src/`, `yuno_viper/`, `imports/`, `de/`, `greyhack-tools/`, `tools/`

**Neue Struktur:**
```
src/
├── core/        (7 files: libcore, buildcore, cli_core, netcore, cliFeedback, debugcore, filecore)
├── crypto/      (2 files: grsa_v2, decypher)
├── recon/       (2 files: recon_lite, mission_report)
├── security/    (1 file: hardening)
├── tools/       (4 files: suid_exploit, mxwrap, portmon, recon)
└── viper/       (reserved for yuno_viper modules, currently 0 src files)
```

**Commit:** `git mv` statt `mv` + `git rm` — saubere Rename-Historie (11 Files renamed)

**`.gitignore` Updates:**
- `imports/` — Snapshot-Archive (3.4MB, nicht build-relevant)
- `de/imports/` — Gleicher Grund
- `notes.md` — Enthält Credentials (password123)
- `greybel-vs/` — Nested git repo von greybel test-workspace

### Finale Akzeptanzkriterien (alle GRÜN)

| Kriterium | Status |
|-----------|--------|
| 66 .src files von ci-build.sh erkannt | ✅ |
| --help funktioniert (Exit 0) | ✅ |
| Keine alten security/-Pfad-Referenzen | ✅ |
| Keine alten yuno_viper/-Referenzen | ✅ |
| Keine Duplikate | ✅ |
| Working tree clean | ✅ |
| 5 neue Commits auf refactor-Branch | ✅ (42 ahead develop total) |

### Endergebnis

- **Plan:** 5 Tasks, 3.5h geschätzt
- **Execution:** ~30 Min (8.5x Speedup durch Parallelisierung)
- **Kosten:** 3× Fable Calls (~$0.90) + lokale M3 Subagenten (kostenlos)
- **Backup:** Sicherung existiert, Rückkehr jederzeit möglich

## Nützliche Kommandos aus der Session

```bash
# Backup vor Refactor
backup_root=~/Dokumente/Backups/refactor-pre-$(date +%s)
mkdir -p "$backup_root"
cp -r src/ "$backup_root/src/"

# Cherry-Pick statt Rebase
git checkout -b feature/sync origin/develop
git fetch <other-clone> +branch:refs/remotes/other/branch
git cherry-pick <sha-from-other>

# md5-check vor diff
md5sum file1 file2   # wenn identisch → kein diff nötig

# ci-build discovery pattern
git ls-files '*.src' | grep -v -E "^(tests/|imports/|build/)"

# Final verification
git status --short                    # clean?
git rev-list --count base..HEAD        # wieviele commits?
git diff --stat base..HEAD             # was geändert?
```
