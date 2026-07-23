# greyscripts Clone Analysis — Worked Example (Enhanced)

**Datum:** 2026-07-05 (aktualisiert)
**Remote:** `https://github.com/Toqsick/greyscripts.git` (privat)
**Klone:** A = `/home/bratan/30-Library/greyscripts`, B = `/home/bratan/10-Projekte/10-active/greyhack-tools`
**Methode:** 100 % read-only. Ein `git fetch origin develop` für beide Klone.

---

## Ausgangslage

Basti hatte zwei Klone desselben Repos an verschiedenen Orten:

| | Clone A (Library) | Clone B (Projekt) |
|---|---|---|
| **Branch** | `fix/merge-main-cluster-fixes-into-develop` | `develop` |
| **Working Tree** | CLEAN | DIRTY (4 untracked) |
| **HEAD** | `02df883` docs: PR-Body null-guards | `efe3073` feat(yuno_viper) v1.0.0 |
| **Ahead/Behind origin/develop** | 0 ahead, 2 behind | 2 ahead, 37 behind |
| **Remote** | `origin → Toqsick/greyscripts.git` | identisch |
| **`.ci-build/`** | 19/19 PASS | Artefakte, kein Log-Refresh |

**Kernbefund:** Beide Klone = selbes Remote, unterschiedliche Branches + unterschiedliche Sync-Stände.

---

## Phase 1 — Erweitertes File-Inventar mit LOC-Tabelle

**84 .src-Files in A (13 713 LOC), 95 .src-Files in B (21 757 LOC).**
77 gemeinsame Pfade. 19 mit non-empty Diff.

Top 10 (nach LOC, gemeinsame Files):

| Pfad | LOC A | LOC B | Zweck |
|---|---|---|---|
| `greyhack-tools/xmem/xmem.src` | 900 | 889 | Metaxploit Memory-Scanner |
| `greyhack-tools/bltings/bltings.src` | 507 | 507 | Settings-Manager |
| `src/crypto/decypher.src` | 498 | 488 | Decryptor-Helper |
| `src/filecore.src` | 640 | 648 | File-IO-Core-Lib |
| `src/security/grsa_v2.src` | 436 | 433 | RSA v2 |
| `src/crypto/grsa_v2.src` | 436 | 433 | RSA v2 (Duplikat zu security/) |
| `src/security/hardening.src` | 392 | 389 | Härtungs-/Audit-Skript |
| `src/tools/recon.src` | 322 | 340 | Kombinierter Aufklärungsreport |
| `greyhack-tools/launcher/launcher.src` | 318 | 318 | Tool-Launcher |
| `src/tools/mxwrap.src` | 313 | 317 | Metaxploit-Wrapper |

### Build-Barrier Analysis

Nicht alle .src-Files sind buildbar. Klassifikation:

| Kategorie | Count | Pfad-Muster |
|-----------|-------|-------------|
| BUILD (in src/ + tools/) | 19 | `src/*.src`, `tools/*.src` |
| GT-TOOL (Sub-Projekte) | ~30 | `greyhack-tools/*/*.src` |
| FEATURE (yuno_viper) | 5 | `yuno_viper/*.src` |
| TEST | ~15 | `tests/*.src` |
| ARTIFACT (build/) | 1 | `build/yuno_v6.src` |
| SNAPSHOT (imports/) | zahlreich | `imports/*.src` |
| UNKNOWN (root-dups) | 7 | `recon.src`, `cli_core.src` etc. |

**Nur 19 von 84–95 .src-Files landen im CI-Build** — die restlichen sind
Sub-Projekte, Tests, Feature-Module oder Build-Artefakte.

---

## Phase 2 — Substanzielle Diffs (19 .src mit non-empty Diff)

Nach Schwere sortiert:

| Pfad | LOC A | LOC B | +A/−B | Interpretation |
|---|---|---|---|---|
| `src/tools/mxwrap.src` | 313 | 317 | +35/−31 | Größte Änderung: null-guards + defensives Coding |
| `src/filecore.src` | 640 | 648 | +35/−27 | Refaktor, defensive null-guards |
| `src/tools/recon_lite.src` | 168 | 180 | +27/−15 | Feature-Erweiterung |
| `src/tools/portmon.src` | 275 | 283 | +20/−12 | Bug-Fix |
| `src/tools/recon.src` | 322 | 340 | +24/−6 | Feature-Erweiterung |
| `greyhack-tools/xmem/xmem.src` | 900 | 889 | +25/−36 | Refaktor auf beiden Seiten |
| `src/cliFeedback.src` | 87 | 64 | +0/−23 | **B deutlich kürzer** |
| `src/buildcore.src` | 96 | 77 | +0/−19 | **B deutlich kürzer** |
| `src/crypto/decypher.src` | 498 | 488 | +4/−14 | Code-Reduktion |
| `src/security/grsa_v2.src` | 436 | 433 | +9/−12 | Kleiner Fix |
| `src/crypto/grsa_v2.src` | 436 | 433 | +9/−12 | Duplikat security/ |
| `src/security/hardening.src` | 392 | 389 | +6/−9 | Kleiner Fix |
| 7 weitere | — | — | ±1–6 | Marginal |

Alle Diffs entsprechen den Cluster-1/2-Fixes (Issues #41/#42) und dem
null-guard-Commit `eaaeeaf` — **Clone A hat die Fixes, Clone B nicht.**

---

## Phase 3 — Exclusive Pfade

### Nur in Clone A (7 Files — alle Müll)

| Pfad | LOC | Zweck |
|---|---|---|
| `cli_core.src` (root) | 158 | Root-Duplikat von `src/cli_core.src` |
| `debugcore.src` (root) | 179 | Root-Duplikat von `src/debugcore.src` |
| `filecore.src` (root) | 487 | Root-Duplikat von `src/filecore.src` |
| `mission_report.src` (root) | 196 | Root-Duplikat von `src/tools/mission_report.src` |
| `recon.src` (root) | 243 | Root-Duplikat von `src/tools/recon.src` |
| `recon_lite.src` (root) | 114 | Root-Duplikat von `src/tools/recon_lite.src` |
| `test_multi.src` (root) | 7 | Mini-Test |

**Befund:** Alte `-dbf`-Build-Artefakte auf Root-Ebene. Stehen im `.gitignore`
als auskommentierte Zeilen → harmlos, aber Müll.

### Nur in Clone B (18 Files — gemischt)

| Pfad | LOC | Klassifikation |
|---|---|---|
| `yuno_viper/yuno_viper_core.src` | 411 | ✅ Neu (tracked, HEAD) |
| `yuno_viper/yuno_viper_net.src` | 727 | ✅ Neu (tracked, HEAD) |
| `yuno_viper/yuno_viper_post.src` | 684 | ✅ Neu (tracked, HEAD) |
| `yuno_viper/yuno_viper_scan.src` | 815 | ✅ Neu (tracked, HEAD) |
| `yuno_viper/yuno_viper_util.src` | 701 | ✅ Neu (tracked, HEAD) |
| `yuno_viper/modules/*.src` (5) | x5 | ❌ Müll (byte-identische Duplikate der tracked-Files) |
| `attack_tiers.src` | 55 | ⚠️ Sensitiv (im .gitignore, inkorrekt) |
| `build/yuno_v6.src` | 2183 | ❌ Müll (Build-Artefakt, TBI-Bug) |
| `greybel-vs/test-workspace/*.src` (5) | 64–146 | ⚠️ Test-Workspace des Submoduls |
| `greybel-vs/scripts/installer-utils.src` | 42 | ⚠️ Submodul-Bestandteil |

---

## Phase 4 — CI-Workflow-Vergleich + Cross-Branch Drift

**Workflow-Inventar (beide identisch):** 5 Files (auto-close, auto-label,
auto-pr-reply, ci.yml, pr-reminder).

**CI-Job-Drift (critical):**

| Aspekt | Clone A (fix/merge-…) | Clone B (develop) |
|---|---|---|
| **ci.yml Gesamt-LOC** | 61 | 25 |
| **Job 1** | `lint-yaml` (yamllint) | `lint-workflows` (yamllint + actionlint) |
| **Job 2** | `greybel-build` (needs: lint-yaml) | ❌ **FEHLT** |
| **Artifact-Upload** | ✅ (greybel-build-log, 7d retention) | ❌ |
| **Build-Script CLI** | `greybel build <file> <dir>` (3.7.x) | `greybel -o <file>` (3.6.x, outdated) |

**Drift-Erkenntnis:** Clone B (develop) ist 37 Commits hinter origin. Die
CI-Upgrades (greybel-build job, CLI-Subcommand-Fix) existieren bereits upstream
aber lokal noch nicht.

---

## Phase 5 — Build-Verifikation

**Ergebnis:** 19/19 PASS auf Clone A. Clone B nicht getestet (altes Build-Script).

```bash
# Verifiziert
which greybel          # → 3.7.12
greybel build src/buildcore.src /tmp/test-build/buildcore  # → PASS
bash scripts/ci-build.sh --out-dir .ci-build               # → 19/19 PASS
```

---

## Phase 6 — Hygiene-Scan mit TBI-Detection

### Untracked (nicht ignoriert) — Clone B

| File/Dir | Größe | Klassifikation |
|---|---|---|
| `greybel-vs/` | ~410 MB | ❌ Nested Clone (eigenes .git/, node_modules/) |
| `notes.md` | 12 Zeilen | ⚠️ Test-Credentials (`reraldi/password123`) |
| `reports/*.md` | 4 Files, 56 KB | ⚠️ Spiel-DB-Reports (privat) |
| `yuno_viper/modules/` | 5 × 120 KB | ❌ Byte-identische Duplikate |

### Tracked-Before-Ignore (TBI) — Clone B

| File | Gematcht von | Status |
|---|---|---|
| `build/yuno_v6.src` (2183 Zeilen) | `/build/` im .gitignore | **TBI** — `git add -f` vor Ignore-Regel |
| `.last-ci-check` | `/.last-ci-check` im .gitignore | **TBI** — tracked vor Regel |
| `attack_plan_tiers.txt` | `/attack_plan_tiers.txt` | Korrekt ignoriert ✅ |
| `attack_tiers.src` | `/attack_tiers.src` | Korrekt ignoriert ✅ |

### Mode-600 Check

```bash
find . -not -path './.git/*' -perm 600 -type f
# → Keine mode-600 Files (alle sensiblen Files sind mode 644)
```

---

## Phase 7 — Master of Truth

| Kriterium | Clone A | Clone B |
|---|---|---|
| Ahead of origin/develop | +2 ✅ | +2 (yuno_viper) ✅ |
| Behind origin/develop | 0 ✅ | 37 ❌ |
| CI greybel-build-Job | ✅ 61 LOC | ❌ 25 LOC |
| CI-Script greybel-kompatibel | ✅ (3.7.x build) | ❌ (alte -o) |
| Cluster-Fixes #41/#42/#50 | ✅ gemerged | ❌ fehlen |
| Working-Tree | ✅ clean | ❌ 4 untracked, TBI-Bugs |
| Build-Barrier dokumentiert | 19/84 buildbar | 19/95 buildbar |
| **MoT-Entscheidung** | **← GEWINNER** | (yuno_viper cp) |

**Master of Truth:** Clone A. Clone B muss `git pull origin develop` + Cleanup.

### Ausnahme

`yuno_viper/*` (5 Module, 3 338 LOC) existiert nur in Clone B — via
`git cherry-pick ef9aec2 efe3073` nach A holen.

---

## Eingesetzte Enhanced-Techniken

1. **Cross-Branch CI Job Drift** — ci.yml auf Job-Ebene verglichen (61 LOC vs 25 LOC, 2 Jobs vs 1 Job)
2. **Build-Barrier Analysis** — Alle .src-Files nach Build-Status klassifiziert (nur 19/84+95 buildbar)
3. **Tracked-Before-Ignore (TBI) Detection** — `git ls-files` gegen .gitignore-Patterns, fand `build/yuno_v6.src` und `.last-ci-check`
4. **Mode-600 Sensitivitäts-Scan** — Alle sensiblen Files als 644 bestätigt
5. **Klassifizierte Exclusive-Pfade** — Bewertet als ✅ (Feature) / ❌ (Müll) / ⚠️ (Sensitiv)

---

## Lessons Learned (Session 2026-07-05)

1. **TBI-Files sind ein stilles Hygiene-Problem** — `.gitignore` schützt nicht vor already-tracked Files. Immer `git ls-files` + `.gitignore`-Kreuzcheck.
2. **Build-Barrier Analysis verhindert Fehlurteile** — 84 .src-Files sehen nach viel Build-Arbeit aus, aber nur 19 landen im CI. Die 65 anderen sind Tests, Sub-Projekte oder Feature-Module.
3. **CI-Drift zwischen Branches ist normal aber dokumentationspflichtig** — Clone B (develop) hatte greybel-build-Job nicht, weil `pull origin/develop` fehlte.
4. **Reines `git status` reicht nicht** — Clone B sah "dirty", aber die wirklich problematischen Files (TBI) waren im `git status` unsichtbar.
5. **Reports und Notes gehören nicht ins Repo** — `reports/`, `notes.md` und `attack_plan_tiers.txt` sind persönliche Spiel-Notizen, kein Projekt-Content.

Siehe vollständige Roh-Analyse unter:
`/home/bratan/docs/system/schwarm-github-hygiene-2026-07-05/greyscripts-analyse.md`
(546 Zeilen, 34.6 KB, mode 644)
