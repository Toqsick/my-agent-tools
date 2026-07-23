# Bug Patterns NP-74–NP-78 — Refactor + Distiller Round (2026-07-05)

> **Session:** Toqsick/greyscripts Refactor-Execution + Knowledge-Distiller KW28
> **Quell-Doku:** `~/docs/system/refactor-execution-2026-07-05.md`, `~/docs/system/github-hygiene-execution-2026-07-05.md`, `~/.hermes/skills/gaming/greyhack-greyscript/references/yuno-viper-build-breaker-audit-2026-07-04.md`
> **Abgrenzung:** NP-69–NP-73 sind in `bug-patterns-2026-07-04-knowledge-distiller.md`. Diese Datei setzt chronologisch fort.

---

### Pattern NP-74: `hermes-v7-orphan` Clone hatte Token embedded in Remote-URL

- **Discovery:** Fable 2 Schwarm-Scan (GitHub-Hygiene, 05.07.2026)
- **Symptom:** Git-Remote-URL enthält direkt ein `gho_*`-Token statt SSH oder HTTPS mit gh-cli-Auth
- **Risiko:** Jeder Clone/PR/Fork exponiert das Token. GitHub markiert `gho_` als möglichen Leak in Push-Hooks
- **Mitigation:** SSH-Remote umstellen: `git remote set-url origin git@github.com:owner/repo.git` + `gh auth login` neu
- **Nachkontrolle:** `git remote -v` → muss `git@github.com:...` zeigen, kein `https://gho_...@github.com/...`
- **Status:** ✅ SSH-Fix applied · ⚠️ Token-Revoke in **https://github.com/settings/tokens** ist manuelle Basti-Aktion
- *Quelle:* `~/docs/system/github-hygiene-execution-2026-07-05.md:18-22`, `~/docs/system/schwarm-github-hygiene-2026-07-05/MASTERPLAN-FABLE-5.md:18-30`

---

### Pattern NP-75: YUNO VIPER One-Line-If Massen-Befund (284 Zeilen)

- **Discovery:** Build-Breaker-Audit (06:14, 04.07.2026) — 5 Module / 3008 Zeilen gescannt
- **Symptom:** 142 einzeilige `if X then Y end if` in VIPER-Modulen (davon 81 in `yuno_viper_net.src` allein). Greybel-js rejected die Syntax, in-game GreyScript toleriert sie
- **Mitigation:** Python-Regex-Batch-Conversion (im Audit-Doku-Doc enthalten) expandiert alle zu Multi-Line. Vor VIPER-V2-Build laufen lassen
- **Drei Varianten:**
  1. Pure one-line-if: `if v == null then v = "[null]" end if` → einfache Expansion
  2. Statement-chain: `if not ports then warn("x"); exit end if` → `;` in separate Zeilen splitten
  3. Combined termination: `if Dp then for Cd in Dp ... end for end if` → zwei `end` auf einer Zeile
- **Auto-Fix-Script:** Python Regex expandiert `^(\s*)if\s+(.+?)\s+then\s+(.+?)\s+end\s+if\s*$`, Backup + Verify (siehe `build-ci-fix-2026-06-19.md`)
- **Status:** ⚠️ Skript existiert (im Audit-Doku-Doc), **noch nicht auf VIPER-Module angewendet**
- *Quelle:* `~/.hermes/skills/gaming/greyhack-greyscript/references/yuno-viper-build-breaker-audit-2026-07-04.md:11-18, 27-42`

---

### Pattern NP-76: `ci-build.sh` basierte auf brittle `find` — brach nach Verzeichnis-Refactor still

- **Discovery:** Task 5 der Refactor-Execution (05.07.2026)
- **Symptom:** `find src/ -name "*.src"` traf nach `src/{core,crypto,recon,tools,viper}/`-Restrukturierung nur noch 12/66 Files. CI blieb grün weil die fehlenden 54 Files keinen Build-Trigger hatten → **stille Regression**
- **Root Cause:** `find` traversiert rekursiv ab `src/`. Nach dem Split in Subdirs fand der Glob nur Dateien im Wurzel-`src/`, nicht in den neuen Unterverzeichnissen
- **Mitigation:** Komplett neuer `ci-build.sh` (3360 bytes) mit:
  - `git ls-files`-basierter Discovery (erfasst alle tracked `.src` Dateien unabhängig von Verzeichnisstruktur)
  - Mock-Build Fallback ohne greybel (gibt Statusmeldung wenn greybel nicht installiert)
  - `--dry-run` Modus (listet Files ohne zu builden)
  - Verbose/quiet modes
- **Verifikation:** `./ci-build.sh --dry-run` → zählt 66 Files
- **Status:** ✅ Fixed + committed (`4d9ff4b fix(ci): unified ci-build.sh v2`)
- *Quelle:* `~/docs/system/refactor-execution-2026-07-05.md:24-28`, `~/docs/system/refactor-masterplan-2026-07-05.md:13-17`

---

### Pattern NP-77: DB-Snapshot-Watchdog erkennt keine historischen Deltas

- **Discovery:** Distiller-Cross-Check (05.07.2026) — 5 neue DB-Snapshots waren alle identisch
- **Symptom:** `db-state.json` speichert Hash-Baseline des jeweils letzten Snapshots. Wenn `db-state.json` selbst nicht aktualisiert wird (z.B. weil Cron nur den aktuellen Snapshot loggt), ist kein historischer Vergleich möglich
- **Konsequenz:** Watchdog funktioniert für **Current-vs-Last** (silent wenn identisch). Für Wochen-Vergleiche ("Was hat sich seit Montag verändert?") braucht es einen separaten Distiller-Pass, der zwei Snapshots direkt vergleicht
- **Mitigation:** Distiller-Phase-2 implementiert `scripts/distiller-counts.py` und `scripts/distiller-files-delta.py` für direkten Snapshot-Paar-Vergleich. Kein Watchdog-Ersatz nötig — die Tools sind komplementär
- **Status:** ✅ Erkannt und dokumentiert · Watchdog verhält sich korrekt (keine False-Alarms)
- *Quelle:* `~/.local/share/maxclaw/db-state.json` (Stand 2026-07-05 22:01), `~/20-Workspace/results/greyhack-weekly-insights-2026-07-05.md` (Quellen-Index)

---

### Pattern NP-78: `notes.md` Secret-Leak in Git-Working-Tree

- **Discovery:** P0.4 GitHub-Hygiene Triage (05.07.2026)
- **Symptom:** `notes.md` (222 B) in `10-Projekte/.../greyhack-tools/` enthielt `password123` + Kontonummern im Working-Tree. File war **bereits im Git-Index** (Commit `7667000 chore(workspace): role documentation + reports staging`)
- **Risiko:** Secrets sind in der Git-History for alle Ewigkeit sichtbar. Jeder Fork/Clone hat Zugriff
- **Mitigation Stufe 1:** File zu `.gitignore` hinzugefügt → verhindert neue Commits mit diesem File
- **Mitigation Stufe 2 (noch offen):** `git filter-repo` oder `bfg-repo-cleaner` notwendig, um die Secrets aus der Git-History zu tilgen. Einfaches `git rm --cached` reicht nicht!
- **Vorsicht:** `git filter-repo` rewrited History — alle Collaborator-Clones müssen neu gebranched werden
- **Status:** ⚠️ Teil-Fix (`.gitignore` applied), volle History-Sanierung offen
- *Quelle:* `~/docs/system/github-hygiene-execution-2026-07-05.md:42-46`
