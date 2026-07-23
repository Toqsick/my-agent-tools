# hermes-v7 4-Clone Analyse — Multi-Clone Worked Example

**Datum:** 2026-07-05
**Remote:** `https://github.com/Toqsick/hermes-v7.git`
**Klone:** C1–C4 über 3 Workspace-Bereiche verteilt
**Methode:** Read-only. Subagent via delegate_task (MiniMax-M3, 290s)

---

## Ausgangslage

Vier lokale Klone desselben Remotes, über drei Workspace-Bereiche verteilt:

| # | Pfad | Branch | Stand |
|---|------|--------|-------|
| 1 | `30-Library/hermes-v7/` | `feat/security-kernel` | 04.07 — aktuellster |
| 2 | `10-Projekte/20-experimental/hermes-v7-wt/` | `feature/yuno-mobil-setup-bundle` | 04.07 |
| 3 | `10-Projekte/20-experimental/hermes-v7-orphan/` | `main` (lokal alt) | 03.07 🚨 |
| 4 | `10-Projekte/40-archive/hermes-zorin/` | `Zorin-Hermes-alt` | 28.06 |

**Pfad-Korrektur:** Clone 4 lag in `40-archive/` nicht `40-experimental/`.

---

## Schlüsselfunde

### 1. Token-Leak in Clone 3 🚨

`https://Toqsick:gho_2X...Lz1g@github.com/Toqsick/hermes-v7.git`
- Klassischer GitHub OAuth User Token (40 Zeichen, `gho_*`)
- `.git/config` Mode **664** (group-readable)
- **Gesamtrisiko:** Mittel. Token seit 03.07. im Klartext auf einer Multi-User-Box.

**Sofortmassnahmen (User):**
1. Token revoken unter `https://github.com/settings/tokens`
2. Remote-URL auf `https://github.com/Toqsick/hermes-v7.git` setzen
3. `.git/config` auf Mode 600 setzen
4. `git credential.helper libsecret` global einrichten

### 2. Clone-Inventar: Was existiert wo

| Komponente | C1 | C2 | C3 | C4 |
|------------|:--:|:--:|:--:|:--:|
| `src/` | ✅ | ✅ | ❌ | ✅ |
| `cli/` | ✅ | ✅ | ❌ | ✅ |
| `.github/workflows/` | ✅ | ✅ | ❌ | ✅ |
| Test-Files | **11** | 9 | 0 | 0 |
| Tracked Files | 8066 | 8070 | 192 | 7847 |

### 3. Exklusive Features

**Nur in C1:** SecurityKernel (4-Ebenen-Fail-Closed, tests/kernel.test.ts)
**Nur in C2:** Yuno-Mobil Setup-Bundle (8 Files, Build-Script)
**Nur in C3:** Nichts Wertvolles (abgespeckte Skill-Kopie)
**Nur in C4:** 3 ADRs (001-003), Depp-Worker, V1-Architektur, Dashboard, systemd-Unit

### 4. Hygiene

**C1:** `logs/audit.jsonl` untracked — **nicht in .gitignore** (sollte `logs/*.jsonl`)
**C2:** ✅ sauber
**C3:** 🚨 Token-Leak (s.o.)
**C4:** ✅ Archiv, keine Hygieneprobleme

---

## Empfehlung (Konsolidierung)

1. **C3 entsorgen** (nach Token-Revoke + Quarantäne)
2. **C1 als Working-Copy** behalten (einziger mit security-kernel + Tests)
3. **C2 als Feature-Branch** behalten (yuno-mobil-setup auf main-Stand)
4. **C4 als Archiv** behalten (`40-archive/`, kein aktiver Workflow)
5. `.gitignore` um `logs/*.jsonl`, `auth.json`, `.netrc`, `*.token` erweitern
6. Alle `.git/config` auf Mode 600 setzen

---

## Lessons Learned

1. **4 Klone = 4x Remote, 4x Branch-Liste.** Systematisch per Loop durchgehen.
2. **Mode 664 auf .git/config ist kein Bug, sondern ein Risiko.** Jeder Prozess
   mit Gruppen-Lese-Recht hat den Token.
3. **Clone 4s Pfad war falsch angenommen** (`40-archive/` ≠ `40-experimental/`).
   Subagent hat korrigiert — read-only heisst auch Pfade validieren.
4. **Untracked audit.jsonl = wächst pro Tool-Call.** Sofort ins .gitignore.
5. **C3 als "orphan" mit 192 Files vs C1 mit 8066** — klarer Indikator für
   abgespeckten/frühen Clone.

Siehe vollständige Roh-Analyse:
`/home/bratan/docs/system/schwarm-github-hygiene-2026-07-05/hermes-v7-multi-clones-analyse.md`
(391 Zeilen, 21 KB, mode 600)
