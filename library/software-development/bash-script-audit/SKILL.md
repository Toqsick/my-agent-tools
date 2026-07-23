---
name: bash-script-audit
title: Bash Script Audit & Hardening
description: "Use when user asks to audit or harden Bash scripts, scan shell code for bugs and security issues, run ShellCheck-style analysis, or repair Bash blocks embedded in Markdown skills. NOT for writing a new script from scratch or reviewing application code. Inventories scripts, applies targeted fixes, runs syntax and dry-run checks, and verifies regressions."
tags:
- bash
- auditing
- shell-script
- hardening
- security
- markdown
- severity-scan
triggers:
- User asks for "bug search" or "script review" on shell scripts
- User wants to audit ~/bin/ or custom script directories
- Discovering and fixing common bash pitfalls (YAML-sed, dead paths)
- Proactive system maintenance of user-created scripts
- Missing set -euo pipefail in SKILL.md Bash-Blöcke
- Severity-Scan produces "broken link" or "missing set -e" findings — need to distinguish
  real issues from False Positives
version: 1.1.0
author: Hermes Agent
license: MIT
lane:
- worker-heavy
- gate
reasoning_effort: xhigh
trigger_keywords: ['and', 'bash', 'scripts', 'code', 'bash-script-audit']
keywords: ['bash', 'scripts', 'code', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

# Bash Script Audit & Hardening

## Overview

Proactively find and fix bugs in bash scripts *before* they cause problems.
Unlike reactive debugging (error → investigate → fix), this is a systematic
audit: inventory all scripts, analyze each one, fix issues, verify the result.

**Two scopes:**
1. **Real .sh scripts** in `~/bin/`, `~/.local/bin/`, custom tool dirs
2. **Markdown Bash-Code-Blöcke** in `~/.hermes/skills/**/SKILL.md` (set -euo pipefail Guards)

**Both scopes share the same workflow:** inventory → analyze → fix → verify.

## Workflow

### Phase 1: Inventory

Find all bash scripts across relevant directories:

```bash

set -euo pipefail
# ~/bin/ (user scripts)
ls -la ~/bin/*.sh

# Custom tool directories
ls ~/greyhack-tools/*.sh

# Broader search
search_files(path="/home/bratan", pattern="*.sh", target="files")
```

For Markdown-Scope: extract findings from a Lane-1C-style severity scan
(`p1-item4-pipefail-list.json` with 'path' fields).

Check for:
- Executable scripts (`chmod +x`)
- .sh extension vs shebang-only scripts
- Scripts in PATH (`~/bin/`, `~/.local/bin/`)
- Bash code blocks in SKILL.md without `set -e` guard

### Phase 2: Analysis

#### 2a. ShellCheck (if available)

```bash

set -euo pipefail
shellcheck ~/bin/*.sh
```

If not installed: `apt install shellcheck` or manual review.

#### 2b. Manual Pattern Scan — Common Bash Bugs

| # | Bug Pattern | Symptom | Fix |
|---|-------------|---------|-----|
| 1 | **YAML-sed** | `sed -i 's/^  provider:.*/.../' ~/.hermes/config.yaml` matched multiple lines | Use Python yaml.safe_load/dump instead |
| 2 | **Dead code paths** | Script tries to start removed service (Ollama, old daemon) | Remove or add check |
| 3 | **Outdated commands** | CLI binary renamed or flags changed | Update to current syntax |
| 4 | **Duplicate scripts** | Two scripts do same thing with different values | Consolidate, delete duplicate |
| 5 | **Double-eval of dynamic commands** | `$(cmd)` evaluated twice (e.g. `cp file-$(date +%s) && echo "backup: file-$(date +%s)"`) | Store in variable first: `f="file-$(date +%s)"; cp "$f" && echo "$f"` |
| 6 | **Missing dependencies** | Script calls tool not installed | Add check + error message |
| 7 | **Race conditions** | No wait-loop before hardware/dependency is ready | Add poll-with-timeout |
| 8 | **Hardcoded paths** | `/home/bratan/...` instead of `$HOME` | Use `$HOME` or `~` |
| 9 | **Error handling** | `set -e` missing, no error checks | Add `set -euo pipefail` |
| 10 | **Config drift** | Script references old config keys or file paths | Audit and update references |
| 11 | **Unused variables** | Defined but never referenced | Remove or document intent |
| 12 | **`set -e` + side-effect in success path** (gefunden 2026-06-08) | `set -e` killt das Script wenn nach einem erfolgreichen Schritt ein sekundärer Call (z.B. `stats`, `cleanup-log`) failed. Erfolgreicher Hauptschritt wird als Fehler geloggt. | Sekundäre Calls mit `\\|\\| true` isolieren oder in `if`-Block verschieben. Beispiel: `hermes stats 2>&1 \\| head -10 >> "$LOG" \\|\\| log "WARNING: stats failed (sleep itself was ok)"` |
| 13 | **`cp` als SQLite-Backup-Fallback** (KRITISCH, gefunden 2026-06-08) | `cp db.db backup.db` während eines laufenden Write-Vorgangs (z.B. Sleep-Job, WAL-Checkpoint) produziert **konsistent korrupte Backups** (mid-WAL-page-copy). `set -e` verhindert das nicht, weil `cp` Exit 0 zurückgibt. | **cp-Fallback komplett ENTFERNEN.** Stattdessen `sqlite3 db.db ".backup 'backup.db'"` als MUST, dann `PRAGMA integrity_check` zur Verifikation. Falls sqlite3 nicht verfügbar: **FAIL mit Exit 2** (kein silent corrupt backup). |
| 14 | **Backup-Verifikation: nur `[ -f ]`** (gefunden 2026-06-08) | Ein leerer 0-Byte-Backup würde "OK" melden. Ein cp-Abbruch nach 50% liefert eine unbrauchbare Datei mit positiver Size. | Mindestgröße prüfen (z.B. `[ "$SIZE" -lt 1024 ]`) UND `sqlite3 backup.db "PRAGMA integrity_check;"` muss `"ok"` zurückgeben. Sonst `rm -f` und exit. |
| 15 | **flock-Pattern falsch** (gefunden 2026-06-08) | `flock -n` ohne korrektes fd-Setup greift nicht. `flock(2)` (fcntl) und `flock(1)` (Tool) sind **nicht kompatibel** — Locking via Python-`fcntl.flock` blockt `flock(1)`-Acquires nicht. | Korrektes Pattern: `exec 9>"/tmp/script.lock"; flock -n 9 && ...` (Write-Open + flock auf fd 9). Sub-Prozess muss `flock(1)` nutzen, NICHT Python-`fcntl.flock`. |
| 16 | **`$?` mit `set -o pipefail`** (gefunden 2026-06-08) | `$?` nach `cmd1 \\| cmd2` gibt den Exit-Code des **letzten** Pipe-Segments (cmd2), nicht den ersten failed (cmd1) wenn pipefail aktiv. Falscher Exit-Status wird geloggt. | `${PIPESTATUS[0]}` explizit für den ersten/gewünschten Befehl. Beispiel: `cmd1 2>&1 \\| tee -a "$LOG"; EXIT=${PIPESTATUS[0]}` |
| 17 | **`cd` ohne Error-Check** (gefunden 2026-06-08) | `cd /path` mit `set -e` killt das Script, aber der Error-Log wird nie geschrieben (Logfile endet mit "started" ohne "FAILED"). Fehlersuche unnötig erschwert. | `cd "$DIR" \\|\\| { log "ERROR: Cannot cd to $DIR"; exit 1; }` |
| 18 | **Cron-Script: System-Deps nicht in venv** (gefunden 2026-06-08) | `sqlite3`, `jq`, `curl` etc. sind **nicht** im Python-venv. `python3 -m ensurepip` installiert sie nicht. Cron-Scripts die darauf zugreifen, schlagen täglich fehl. | Im Script: `if ! command -v sqlite3 >/dev/null; then log "ERROR: sqlite3 missing — apt install sqlite3"; exit 2; fi`. Setup-Doku: `apt install sqlite3` als Pflicht-Schritt listen. |
| 19 | **Array/Variable nach Arg-Parsing definiert** (gefunden 2026-07-04) | `--list` zeigt leer, weil `JOBS`-Array erst NACH der `while [[ $# -gt 0 ]]`-Schleife deklariert wurde, die `${JOBS[@]}` liest. Script parst Argumente bevor Daten existieren. | **Arrays und Konfig-Variablen IMMER VOR der Arg-Parsing-Schleife definieren.** Reihenfolge: `declare -a JOBS=(...)` → `while [[ $# -gt 0 ]]; do ...` → Rest. `bash -n` erkennt den Fehler NICHT (Variable existiert zur Parse-Zeit), aber zur Laufzeit ist sie leer. Gegencheck: `bash -x script.sh --list` zeigt `JOBS[@]` als leer. |
| 20 | **JSONL-Tempdatei wird bei jedem Funktionsaufruf getruncated** (gefunden 2026-07-04) | `: > "$tmp_findings"` am Anfang einer Funktion, die in einer Schleife aufgerufen wird. `: >` truncat die Datei bei jedem Aufruf → nur der letzte Eintrag berlebt. Symptom: N Findings gemeldet, aber JSON-Output enthlt nur 1-2. | **Fix:** `[[ ! -f "$tmp_findings" ]] && : > "$tmp_findings"`. Datei nur beim ERSTEN Aufruf leeren; alle weiteren hngen mit `>>` (append) an. Gegencheck: `wc -l /tmp/.findings-$$.jsonl` vor/nach der Schleife. |
| 21 | **Shell env-var-Name mit readonly-Bash-Variable kollidiert** (gefunden 2026-07-04) | Variable als `readonly REPORT_LAST` deklariert. `REPORT_LAST="$REPORT_LAST" python3 - ...`: Bash exportiert nicht als Env-Var, da `readonly` blockiert. Python erhalt `KeyError: REPORT_LAST`. | **Fix:** Anderen Namen: `REPORT_LAST_PATH="$REPORT_LAST" python3 - ...`. Python liest `os.environ["REPORT_LAST_PATH"]`. `bash -n` erkennt Fehler NICHT. Gegencheck: `env -i REPORT_LAST=val python3 -c "import os; os.environ['REPORT_LAST']"` wirkt KeyError. |
| 22 | **`((VAR++))` Post-Increment unter `set -euo pipefail`** (gefunden 2026-07-07, NP-99) | Counter `VAR=0` initialisiert, dann `((VAR++))` im Loop. `set -euo pipefail` wertet die Expression als Command aus: bei `VAR=0` ist der Return-Wert 1 ("value is 0"), was als Fehler gilt. **Script bricht nach dem ersten Loop-Iteration ab** obwohl die Logik korrekt ist. Bei CI-Build-Scripts maskiert dies reale Build-Failures: das Script "behauptet" `Build done` nach 1 File obwohl 65/66 nie gebaut wurden. | **Fix:** Pre-Increment nutzen: `((++VAR))` (Return-Wert ist immer der neue Wert ≠ 0), ODER explizit: `VAR=$((VAR+1))`. Plus: alle Counter-Inkremente mit `\\|\\| true` wickeln wenn auch Failure toleriert werden soll. CI-Logs IMMER stderr separat nach temp-file umlenken (`err_log=$(mktemp); cmd 2>"$err_log"`), im Fehlerfall erste 3 Zeilen ausgeben — sonst schluckt `2>/dev/null` die echte Fehlermeldung und CI loggt fake-grün. Gegencheck: `bash -x script.sh` zeigt sofort "((VAR++))" mit Exit-Code 1 als erste Iteration. |
| 23 | **`shell_single_quote()` auf Pfade mit `$VAR`-Expansion** (gefunden 2026-07-11, kvo-orchestrator Audit) | Python-Generator (`bootstrap_pipeline.py` o. ä.) baut ein Setup-Script und quotet Zielpfade wie `$WORKSPACE/audio/track.mp3` per Single-Quote. Beim Lauf sieht Bash `'$WORKSPACE/audio/...'` und **expandiert die Variable NICHT** — `cp` legt eine Datei namens `$WORKSPACE/audio/track.mp3` (literal) an und crasht mit "Datei oder Verzeichnis nicht gefunden". Symptom: Setup bricht direkt beim Asset-Copy ab, **bevor** der initiale Director-Task gefeuert wird. Im Trockenlauf reproduzierbar mit Fake-Hermes + Dummy-Assets. | **Fix:** Zwei Quoting-Helper getrennt halten: `shell_single_quote(s)` für **User-/Plan-Pfade** (niemals expandieren, niemals Quoting-Sonderfälle vergessen) und `shell_double_quote_expand_vars(s)` für **generator-eigene Destination-Pfade** mit `$VAR`. Double-Quote-Version muss `\`, `"`, `` ` `` escapen — nie blind `f'"{s}"'` schreiben. Gegencheck: im generierten `setup.sh` mit `grep "'$WORKSPACE"` suchen — Treffer mit `'…$WORKSPACE…'` ist der Bug. |
| 24 | **Generator-Scripts ohne Owner-Marker überschreiben fremde Resources** (gefunden 2026-07-11, kvo-orchestrator Audit) | `hermes profile create foo --clone 2>/dev/null \|\| true` macht **keinen** Konflikt-Check. Wenn `foo` schon existiert (User-Profil mit Skills/Env/History), klont der Generator drüber oder der zweite Create-Command läuft ins Leere. Generierte Scripts, die Profile/Directories/Tenants anlegen, brauchen eine Markierung "dieses Resource gehört Projekt X", sonst kollidieren Re-Runs und Mehr-Projekt-Setups. | **Fix:** Owner-Marker-Pattern: bei jedem generator-erzeugten Resource eine Datei `…/.kanban-video-orchestrator-owner` (oder generischer Marker) mit dem Projekt-Slug anlegen. Beim Re-Run prüfen: Marker fehlt → echt neu anlegen mit Warnung ("Resource existiert und ist nicht owned by this pipeline, rename or back up"). Marker stimmt → idempotent weitermachen. Marker stimmt nicht → harter Abbruch (`exit 1`) statt silent overwrite. Marker erst NACH erfolgreichem `hermes profile create` schreiben, sonst zeigt er auf einen halb-erzeugten Zustand. |

#### 2c. Critical Pattern: YAML Editing via sed

This is the most dangerous bash antipattern. **Never edit YAML with sed.**

**Why sed on YAML is broken:**
- A `provider:` key appears 18+ times in a typical Hermes config.yaml (model, fallback_providers, auxiliary.*, security, etc.)
- `sed 's/^  provider:.*/.../'` matches MULTIPLE unintended lines
- YAML indentation levels differ — `^  ` (2 spaces) != `^    ` (4 spaces)
- Multi-line values and YAML anchors break sed patterns

**Safe alternative — Python yaml:**
```python
import yaml
with open('$CONFIG') as f:
    cfg = yaml.safe_load(f)
cfg['model']['provider'] = 'nous'
with open('$CONFIG', 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False)
```

set -euo pipefail
**In a bash script, embed via heredoc:**
```bash
python3 -c "
import yaml
with open('$CONFIG') as f:
    cfg = yaml.safe_load(f)
cfg['model']['provider'] = '$VALUE'
with open('$CONFIG', 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
"
```

set -euo pipefail
Also check `yq` as a CLI alternative on systems where it's installed.

### Phase 3: Fix

For each bug found:

1. **Read the full script** — understand context before changing
2. **Apply targeted fix** — one bug per change
3. **Verify the fix** — run the script (or syntax-check)

Common fix approaches:

```bash
# Syntax check
bash -n script.sh

# Dry-run for scripts that accept --dry-run
bash script.sh --dry-run

# For config-modifying scripts: check config before and after
diff <(cat config.yaml) <(bash script.sh && cat config.yaml)
```

set -euo pipefail
### Phase 4: Verification

```bash
# All scripts parse correctly
for f in ~/bin/*.sh; do
    bash -n "$f" || echo "SYNTAX ERROR: $f"
done

# Run the modified script
bash ~/bin/modified-script.sh

# Check for regressions
hermes status
hermes cron list  # check cron jobs still work
```

## Markdown-Bash-Code-Block Scope (V7.2, 2026-06-30)

HermesV7 SKILL.md-Dateien enthalten oft ```bash Code-Blöcke ohne `set -euo pipefail`
Guard. Lane 1C Severity-Scan hat das gefunden — Issue-Schätzung lag bei 50 Blöcken,
echter Scope war **3.877 Blöcke in 278 Skills** (77x größer!).

**Lesson: Issue-Schätzungen sind konservativ — DRY-RUN vor APPLY!**

### Auto-Fixer: `scripts/markdown-pipefail-fixer.py`

```bash
# Dry-run (empfohlen zuerst)
python3 scripts/markdown-pipefail-fixer.py
# Output: "Total Bash-Blöcke gefixt: 3877 / 0 übersprungen (bereits OK)"

# Anwenden
python3 scripts/markdown-pipefail-fixer.py --apply
```

**Logik:**
- Iteriert über alle SKILL.md-Dateien aus `p1-item4-pipefail-list.json`
- Findet ```bash / ```sh / ```shell Code-Blöcke (non-greedy multiline)
- Wenn erste Zeile KEIN `set -e...` enthält → fügt `set -euo pipefail` ein
- Idempotent: bereits vorhandene Guards werden erkannt und übersprungen

### Beispiel-Diff
```diff
+```bash
+
+set -euo pipefail
+
 memo notes                        # List all notes
 memo notes -f "Folder Name"       # Filter by folder
 memo notes -s "query"             # Search notes (fuzzy)
-```
+```
```

### Verifikation nach Fix
```bash
# Tests laufen noch (relevant für hermes-v7 Plugin-Tests)
cd /tmp/hermes-v7 && npm test -- --testPathPattern=plugins/__tests__/
# Erwartet: 36/36 grün (oder aktueller Stand)

# Stichprobe: 3 SKILL.md prüfen ob Bash-Blöcke jetzt Guards haben
for f in ~/.hermes/skills/apple/apple-notes/SKILL.md \
         ~/.hermes/skills/linux-system/SKILL.md \
         ~/.hermes/skills/security/system-security-audit/SKILL.md; do
  grep -c "set -e" "$f" || echo "MISSING: $f"
done
```

## Severity-Scan False-Positive Pattern (V7.2, 2026-06-30)

**Lesson:** Lane-1C-artige Severity-Scans produzieren oft False Positives bei
Markdown-Doku. Bei 30 "broken relative link"-Findings waren ALLE False Positives
weil der Scanner `[text](path)`-Syntax in Code-Blöcken/Inline-Code/Template-
Placeholdern nicht als Code erkannt hat.

### Workflow: Bevor du einen Bulk-Edit machst

1. **Erst Kategorisierung** mit `scripts/markdown-link-fixer.py`:
   ```bash
   python3 scripts/markdown-link-fixer.py
   # Output: 5 Kategorien (template_placeholder / ellipsis / relative_path /
   #          checkpoint_arg / other) + jeweils Anzahl
   ```

2. **Pro Kategorie: Stichprobe-Beweis** (manuell) — bei relativen Pfaden
   prüfen ob `[text](path)` innerhalb eines ```markdown-Code-Blocks steht:
   ```python
   # Smart-Analyzer prüft automatisch via count('```') % 2
   ```

3. **Entscheidung:**
   - Wenn alle False Positives: **KEIN File-Edit** — Report schreiben war genug
   - Wenn echte broken links: manuell fixen, NIE blind automatisieren

### Kategorien-Checkliste

| Kategorie | Beispiel | Echter Fix nötig? |
|-----------|----------|-------------------|
| `template_placeholder` | `{relative-path}/NN-{type}-{slug}.png` | ❌ Nein (Template-Syntax) |
| `ellipsis` | `[![Build](...)` | ❌ Nein (Inline-Code) |
| `relative_path_in_code` | `GPU-Tuning` im markdown-Code-Block | ❌ Nein (Beispiel-Template) |
| `relative_path` | `Real-Doc` im Fließtext | ✅ Ja — File fehlt |
| `checkpoint_arg` | `[vit_h](checkpoint="...")` | ❌ Nein (Python-Code) |
| `other` | Variable in Code | ❌ Meist Nein (prüfen) |

Vollständige False-Positive-Analyse: `references/severity-scan-false-positives-2026-06-30.md`.

## Pitfalls

1. **Don't fix what isn't broken in production scripts.** If a script works despite a style issue, note it but only fix if it's a real bug or maintenance burden.
2. **Never edit config files with the `patch` tool.** The agent's `patch` tool is blocked for security on `~/.hermes/config.yaml`. Use `hermes config set` or terminal with `sed`/`python3`.
3. **Cron jobs with `Script not found`** — always check whether cron scripts are in `~/.hermes/scripts/` (the cron default path). If a script lives elsewhere, copy it there or fix the cron job.
4. **Always create a backup before modifying scripts that manage config.** Some scripts have `cp` built-in — let those handle it. For manual edits, `cp script.sh script.sh.bak`.
5. **GreyHack `.src` files are not bash.** They're GreyScript (MiniScript 1.5.1). Don't apply bash analysis patterns to them.
6. **SQLite-Backup: niemals `cp`** — siehe Pattern #13 oben. Konsistente Snapshots nur via `sqlite3 .backup` + `PRAGMA integrity_check`.
7. **flock für Race-Conditions immer mit korrektem fd-Pattern** — `exec N<>file; flock -n N`. fcntl.flock aus Python ist NICHT kompatibel (siehe #15).
8. **Sub-Agent Code-Review für komplexe Scripts** — Wenn ein Script > 100 Zeilen oder Cron-relevant ist, delegiere Code-Review an einen Sub-Agent (qwen3.5-9b lokal ist ausreichend). Der Sub-Agent findet systematisch Bugs, die beim manuellen Lesen übersehen werden. Pattern: `delegate_task(goal="Code-Review der 3 Scripts", toolsets=['terminal', 'file'])`.
9. **Markdown-Code-Blöcke brauchen auch `set -euo pipefail`** (gefunden 2026-06-30) — Wenn SKILL.md-Dateien ```bash Code-Blöcke enthalten, fehlt oft der `set -e`-Guard. Mechanisch fixbar mit `scripts/markdown-pipefail-fixer.py`. Lane 1C Severity-Scan nannte 50 Blöcke — echter Scope war 3877 (77x größer!). **Lesson: Issue-Schätzungen sind konservativ — DRY-RUN vor APPLY!**
10. **Severity-Scan False Positives: Markdown-Link in Code** (gefunden 2026-06-30) — Lane 1C hat 30 "broken relative link"-Findings produziert, ALLE waren False Positives weil der Scanner `[text](path)`-Syntax in Code-Blöcken/Inline-Code/Template-Placeholdern nicht als Code erkannt hat. **Lesson: Bevor Bulk-Edits — manuell validieren!** Smart-Analyzer: `scripts/markdown-link-fixer.py`. Vollständige Analyse: `references/severity-scan-false-positives-2026-06-30.md`. Bei Lane-1C-artigen Severity-Scans IMMER erst Kategorisierung + Beweis-Snapshot, dann Entscheidung "do nothing" wenn alle False Positives.
11. **`((VAR++))` Post-Increment + `set -e` = silent loop abort** (gefunden 2026-07-07, NP-99) — Counter `VAR=0` initialisiert, dann `((VAR++))` im Loop. Bei `VAR=0` ist der Return-Wert 1 (Bash semantics), `set -euo pipefail` killt das Script nach der ersten Iteration. Bei CI-Scripts besonders gefährlich: 65/66 Files "gebaut" obwohl nur 1 erreicht wurde. Fix: `((++VAR))` (pre-increment, Return-Wert ≠ 0) ODER `VAR=$((VAR+1))`. Plus: stderr NIE nach `/dev/null` schicken wenn Debugging wichtig ist — `err_log=$(mktemp); cmd 2>"$err_log"; [ $? -ne 0 ] && head -3 "$err_log"`. Pattern #22 in der Pattern-Tabelle oben. Bei jedem Counter-Post-Increment IMMER prüfen ob die Init-Variable 0 ist und `set -e` aktiv.

11a. **`2>/dev/null` in CI-Loop-Scripts schluckt echte Fehler** (gefunden 2026-07-07, NP-100) — Companion zu NP-99: Auch wenn der Counter-Bug behoben ist, maskiert `2>/dev/null` im greybel-Call die echten Build-Errors. CI-Log behauptet "Build done" obwohl 25 von 66 Files fail sind. **Detection-Recipe:** `grep -n '2>/dev/null' <script>` in CI-/Loop-Scripts → jeder Treffer ist verdächtig. **Fix:** stderr separat nach temp-file umlenken: `err_log=$(mktemp); "$GREYBEL" build "$f" "$target" 2>"$err_log"`, im Fehlerfall `head -3 "$err_log" | sed 's/^/        /'` zur sichtbaren Anzeige. **Warum das Pattern so gefährlich ist:** Kombination NP-99 + NP-100 führt zu "best case 1 file built, worst case 0 files built + fake-grüner Log". Im greyhack-tools Repo (Commit 4d9ff4b, 2026-06-25) lief der CI 13 Tage lang mit fake-grün bis zum Bug-Scan 2026-07-07.

## Support-Dateien

- `scripts/markdown-pipefail-fixer.py` — Fixer für `set -euo pipefail` Guards in
  Markdown-Bash-Blöcken. DRY-RUN by default. Fand 3877 Blöcke in 278 SKILL.md-Dateien
  (Issue-Schätzung lag bei 50 — 77x größer!).
- `scripts/markdown-link-fixer.py` — Smart Analyzer für "broken relative link"-
  Findings. Unterscheidet echte broken links von False Positives (Code-Blöcke,
  Inline-Code, Template-Placeholder). Bei 30 Findings: alle False Positives.
- `references/severity-scan-false-positives-2026-06-30.md` — Lane 1C Scanner-Bug-Doku:
  30 Findings waren alle False Positives. Vollständige Kategorisierung + Beweise +
  Workflow für künftige Severity-Scan-Audits.
- `references/bug-fund-2026-06-06.md` — Erste Sammlung von Bash-Bugs aus früheren Audits.