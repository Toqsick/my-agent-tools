---
name: linux-system-maintenance
title: Linux System Maintenance
description: "Use when user asks for building safe Linux cleanup CLI, modular disk-analysis tools, BaseScanner/SafetyManager patterns. NOT for one-off rm commands or non-Linux system maintenance. Build safe, modular system cleanup and disk-analysis CLI tools."
triggers:
- User asks about disk cleanup, CCleaner alternative, or system maintenance
- User wants to free disk space or analyze storage usage
- Building CLI tools that scan and optionally delete files
- Automating apt/journalctl/thumbnail/browser cache cleanup
- Hermes skill for recurring cleanup tasks
- User asks why a log file (syslog, kern.log, auth.log) is unusually large or growing fast
- Disk usage is high (> 75 %) and log files are suspected as main contributor
- logrotate seems broken, skipped, or logs aren't rotating
version: 1.1.0
author: Hermes Agent
license: MIT
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['safe', 'linux', 'cleanup', 'modular', 'disk']
keywords: ['safe', 'linux', 'cleanup', 'modular', 'disk']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['multi-agent-code-gen-pipeline', 'linux-system']
---


# Linux System Maintenance

## Design Principles

1. **Safety-first, always.** Dry-run is the default. Destructive operations require
   explicit confirmation (type "JA" / "YES"). Never delete without showing the user
   exactly what will be removed.
2. **Modular scanners.** Each cleanup domain implements a `BaseScanner` with a
   `scan() → {"name", "icon", "items": [{"path", "size", "category"}]}` interface.
3. **Rich TUI.** Use `rich` for tables, panels, progress spinners, and colored output.
4. **Configurable.** JSON config drives which scanners are active and which paths are
   whitelisted. Never hard-code user paths.
5. **Backup before delete.** Move to `~/.yuno-cleaner/backups/<timestamp>/` instead
   of `rm -rf` when the user hasn't passed `--no-backup`.

## Architecture

```
cleanup_tool/
├── main.py                 # argparse: scan/clean/status
├── modules/
│   ├── base_scanner.py     # ABC: scan(), is_whitelisted()
│   ├── system_junk.py      # APT, journalctl, thumbnails, temp
│   ├── browser_cache.py    # Chrome, Chromium, Brave, Firefox
│   ├── gaming_junk.py      # Steam shadercache, Mesa/NVIDIA shaders
│   ├── duplicate_finder.py # Two-phase (size → hash), parallel
│   ├── large_files.py      # Top-N with max_depth
│   └── package_managers.py # Flatpak unused, Snap old revisions
├── ui/tui.py               # rich Console, tables, confirm prompts
├── utils/safety.py         # SafetyManager: dry_run, backup, delete
└── config/default.json     # per-scanner enable + whitelist
```

## BaseScanner Interface

```python
from abc import ABC, abstractmethod
from pathlib import Path

class BaseScanner(ABC):
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.name = "Unnamed"
        self.icon = "❓"

    @abstractmethod
    def scan(self) -> dict:
        """Return {"name", "icon", "items": [{"path", "size", "category"}]}"""
        pass

    def is_whitelisted(self, path: str) -> bool:
        for pattern in self.config.get("whitelist", []):
            if pattern in path:
                return True
        return False
```

## SafetyManager Pattern

```python
class SafetyManager:
    def __init__(self, dry_run: bool = True, create_backups: bool = True):
        self.dry_run = dry_run
        self.create_backups = create_backups

    def delete_item(self, path: str) -> bool:
        if self.dry_run:
            return True          # Pretend success
        item = Path(path)
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
        return True
```

## Common Cleanup Targets

| Target            | Path                                       | Root? | Cleanup command                                  |
|-------------------|--------------------------------------------|-------|--------------------------------------------------|
| APT cache         | `/var/cache/apt/archives/*.deb`            | ✅    | `apt clean` (preferred over manual delete)       |
| journalctl        | `/var/log/journal/`                        | ✅    | `journalctl --vacuum-time=7d`                    |
| Thumbnails        | `~/.cache/thumbnails`                      | ❌    | Safe to delete entirely                          |
| pip cache         | `~/.cache/pip`                             | ❌    | `pip cache purge`                                |
| Python pycache    | `~/.cache/**/__pycache__`                  | ❌    | Recursive find, safe                             |
| Browser caches    | `~/.config/{google-chrome,BraveSoftware,**}/Cache` | ❌ | Close browser first                       |
| Steam shadercache | `.../steamapps/shadercache`                | ❌    | Regenerates, often 10-50 GB                      |
| Steam downloading | `.../steamapps/downloading`                | ❌    | Incomplete downloads                             |
| Mesa shader cache | `~/.cache/mesa_shader_cache`               | ❌    | Regenerates on launch                            |
| npm cache         | `~/.npm/_cacache/`                         | ❌    | `npm cache clean --force`, often 1-2 GB          |
| Snap revisions    | `snap list --all` disabled                 | ❌    | `snap remove <name> --revision <n>` for each     |
| Evolution mail    | `~/.cache/evolution/`                      | ❌    | IMAP on server, local cache safe to delete       |
| Crash dumps       | `/var/lib/systemd/coredump`                | ✅    | `systemd-coredump`                               |

## CLI UX Pattern (summary)

```python
parser.add_argument("command", choices=["scan", "clean", "status"])
parser.add_argument("--dry-run", "--json", "--notify", "--no-backup", action="store_true")
safety = SafetyManager(dry_run=args.dry_run or args.command == "scan")
```

- `scan` → always dry-run, shows tables, no changes
- `clean` → dry-run unless `--execute`; requires typing "JA" interactively
- `--no-backup` skips safety backup
- `--json` requires `console.quiet = True` (rich's `redirect_stdout` doesn't catch
  scanner output). Workaround in `safety-patterns.md`.
- `--notify` posts compact summary to Telegram. Pattern in `safety-patterns.md`.

## Cleanup Workflow — Execution Order

1. **No-sudo first** — user-writable caches only (npm, pip, thumbnails)
2. **Large data that user explicitly approved** (downloads, documents, game files)
3. **Sudo cleanups** — apt, journal, kernel purge, rc packages
4. **Document results** to `~/docs/system/` for traceability

### Disk Analysis Drill-Down Hierarchy

Wenn der User nach Speicherplatz oder Disk-Health fragt, dieses Muster nutzen:

**Phase 1 — Top-Level Survey (ohne sudo):**
```
du -h --max-depth=2 -x / 2>/dev/null | sort -h | tail -25
du -h --max-depth=2 /mnt/DATA 2>/dev/null | sort -h | tail -25
```
→ identifiziert die 10-15 größten Fresser sofort

**Phase 2 — Drill Down auf Kandidaten:**
```
du -h --max-depth=1 -x /home/bratan/.var/app 2>/dev/null | sort -h | tail -15
du -sh /path/to/suspect 2>/dev/null
```
→ wenn `.var/app` groß ist, in die Apps reinzoomen

**Phase 3 — Sortieren in "löschbar ohne sudo" vs "braucht Entscheidung":**

| Kategorie | Typische Funde | Aktion |
|-----------|---------------|--------|
| 🟢 Sofort löschbar | Crdownload, alte tar.gz nach Extrakte, Trash, Browser-Cache | `rm -v` direkt |
| 🟡 Prüfen & löschen | Alte Backups (BackUp.zip), Android-Studio tar.gz + extrahierter Ordner | Auflisten + fragen |
| 🔴 Programmdaten | Flatpak-Steam 155G, `.var/app/*` Bibliotheken, VMs (Boxes 34G) | NIE ohne Zustimmung |
| 🟣 Sudo benötigt | Journal-Vacuum, APT-Cache, Waydroid-Images, Snap-Revivals | In Sudo-Sammlung packen |

**Phase 4 — Sudo-Sammlung erstellen** (siehe `system-security-audit` Skill, Phase 0
→ "Sudo-Sammlung Pattern"): alle sudo-Befehle aus der Analyse in ein Script mit
Risiko-Sternchen packen.

**Wichtig:** Die Analyse muss **echte Messungen** liefern, keine
Schätzungen. Jede Zahl in der Ausgabe muss aus `du` oder `stat` kommen.
Nicht raten wenn der Befehl ohne sudo fehlschlägt — als „braucht sudo" markieren.

### Log File Runaway Diagnosis (read-only)

Wenn ein Logfile (besonders `/var/log/syslog`) ungewöhnlich groß ist (> 1 GB)
oder innerhalb weniger Tage massiv wächst, nutze die 7-Phasen-Methodik in
`references/log-file-diagnosis.md`:

1. **Sofortbild** — Grösse, Zeilen, birth/modify, rsyslog-Status
2. **Process-Level Byte-Counting** — awk-Tag-Count + Byte-Estimate pro Prozess
3. **Inhaltliche Probe** — Sample + Nachrichtentypen normalisieren
4. **logrotate-Health-Check** — Timer, ConditionACPower, skipped-Einträge im syslog selbst, size-Trigger-Prüfung
5. **Root-Cause** — Extension / Service / Kernel / UFW identifizieren
6. **P0/P1/P2-Bewertung** — Disk-Trend, Dringlichkeit, Handlungsoptionen
7. **Dokumentation** nach `~/20-Workspace/results/`

**Key insight:** Zeilen zählen reicht nicht. Stack-Traces sind oft 10× grösser
als normale Log-Zeilen. Immer `awk -F"$proc"` für Byte-Counting nutzen.
Und: `ConditionACPower=true` auf Notebooks lässt logrotate auf Akku **still**
überspringen — das sieht man nur im syslog selbst, nicht in `/etc/logrotate.conf`.

### Fix Phase After Diagnosis (2026-07-16 Pattern)

Nach der read-only Diagnose folgt die Fix-Phase. Dieses Pattern kommt aus einer
Live-Session mit 3 Fix-Wellen:

| Welle | Ziel | Dauer |
|-------|------|-------|
| Sofort-Hygiene | Disk entlasten, Logrotation forcieren, Journal vacuum | 90 Sek |
| Persistenz | Drop-ins / Konfig-Änderungen die dauerhaft wirken | 5 Min |
| Workaround/Fronting | Service-Verhalten ändern ohne Funktionsverlust | 2 Min |

**Regel: Erklären vor Ausführen.** Bei System-Terminal-Blöcken (sudo, bash,
Konfig-Edit) jeden Befehl kurz erklären bevor der User ihn pastet. Das ist der
Unterschied zu In-Game-Kommandos (siehe `yuno-user-preferences`).

**Block-Vorlage:**
```
### Blockname — Was passiert

| Befehl | Was es macht | Effekt |
|--------|-------------|--------|
| `sudo logrotate -f` | Erzwingt sofortige Rotation aller Logs | 6,4 GB → ~150 KB |
| `sudo journalctl --vacuum-time=7d` | Löscht Journal-Einträge älter als 7 Tage | 998 MB → ~200 MB |

Risiko: null (Standard-Pattern). Reversibel: ja.

```bash
# Kopiere diesen Block ins Terminal
sudo logrotate -f /etc/logrotate.conf
sudo journalctl --vacuum-time=7d
```

**Erwartet:** Disk 82% → ~76%, syslog 1,3 KB.
**Nach Verify:** `df -h /` + `ls -lh /var/log/syslog` zeigen den neuen Stand.
```

#### Rsyslog-Filter-Workaround (für Log-Spam von nützlichen Services)

Wenn ein Service/Extension/Daemon Log-Spam produziert, der Service selbst aber
gebraucht wird: **rsyslog-Filter vor Deaktivierung**.

```
sudo tee /etc/rsyslog.d/00-<service>-bug-suppress.conf >/dev/null <<'EOF'
# Basti YYYY-MM-DD: <service> Bug-Stacktraces filtern (Funktion bleibt)
if $msg contains "<pattern>" then stop
if $msg contains "<pattern2>" then stop
EOF
sudo systemctl restart rsyslog
```

**Verify:**
```bash
tail -20 /var/log/syslog    # prüfen dass keine Treffer mehr kommen
grep -c "<pattern>" /var/log/syslog  # live-check: 0 = Filter wirkt
```

**Wann anwenden:**
- Bürgerlicher Service (Drucker-Extension, Netzwerk-Manager, ...) spammt Logs
- User braucht den Service und will ihn nicht deaktivieren
- Rsyslog 00-prefix-Drop-in filtert früh raus, kaum CPU-Last

**⚠️ PITFALL — Vor Service-Disable: Hardware-Kontext prüfen!**
Basti hat einen A1 Mini 3D-Drucker und nutzt Zorin-printers aktiv. `gnome-extensions disable zorin-printers@zorinos.com` löst „warum die drucker aus ?" aus. Vor jedem Disable-Vorschlag:
1. Memory check: hat Basti Hardware/Accessoires die den Service brauchen?
2. User fragen: „Nutzt du <service> aktiv?"
3. Rsyslog-Filter als Default-Option zuerst anbieten

Wann NICHT: Service ist kritischer Log-Spammer für Sicherheit (UFW, auditd).

#### Typische Fixes nach Log-Diagnose

| Fund | Symptom | Fix | Verify |
|------|---------|-----|--------|
| `ConditionACPower=true` | Rotation skipped alle 24h auf Akku | `/etc/systemd/system/logrotate.service.d/override.conf` mit `ConditionACPower=` (leer) | `systemctl show logrotate.service \| grep Condition` → nichts |
| Kein size-Trigger | Log wächst > 1 GB zwischen weekly Runs | `size 500M` in `/etc/logrotate.d/rsyslog` vor `weekly` | `logrotate -d /etc/logrotate.conf 2>&1 \| grep -A 2 'considering log'` |
| Extension-Spam | 99% Logs von gnome-shell-Extension | Rsyslog-Filter (oben) oder Extension disable (nur nach User-Freigabe) | `grep -c "<pattern>" /var/log/syslog` nach restart = 0 |
| Gateway auf `0.0.0.0` | Hermes Gateway lauscht Welt-erreichbar auf Port 8642 | UFW-Fronting: `ufw allow from 100.64.0.0/10 to any port 8642` + `ufw default deny incoming` | `ufw status verbose \| grep 8642` |

**Wichtig:** Nach jedem Fix einen Verify-Schritt anhängen (Befehl + Erwartung).
Nicht blind applyen und "done" sagen. Basti's Live-Output beweist es: er pasted
den Verify-Befehl direkt nach dem Fix.

### Critical Workarounds (pointers)

- **rc Package Purge** — `apt autoremove --purge` does NOT clean rc-state packages.
  Use explicit `dpkg --purge` in strict order (kernels → modules → NVIDIA → rc-pass).
  See `cleanup-procedures.md`.
- **steam-installer postrm** — debconf dialog fails in non-TTY. Remove the
  postrm/prerm scripts first, then `dpkg --purge --force-all`. Steam data in
  `~/.steam/` is unaffected. See `cleanup-procedures.md`.
- **Mail client detection** — users say "Thunderbird" but often use Evolution/Gmail
  IMAP (server-side, nothing to clean). See `cleanup-procedures.md`.

For a worked inspection → cleanup → documentation example (~30 GB reclaimed), see
`references/system-inspection-2026-06-03.md`.

## Critical Warnings

- **Never recurse into `~/.ssh/`, `~/.gnupg/`, `~/.config/` blindly.** Whitelist
  specific subdirectories.
- **Browser caches must only be cleaned when the browser is closed.**
- **Steam shadercache regenerates** — warn user about longer first-launch.
- **journalctl requires root** — silently skip or warn if non-root.
- **Syslog self-resolution (2026-07-11 Lesson):** Wenn ein Audit 10+ GiB syslog+syslog.1 meldet, NICHT sofort `truncate -s 0`. Logrotate oder die verursachende Extension kann sich innerhalb von 2h selbst auflösen. **Before truncation:** 30-60min abwarten + re-messen. Passiert keine Selbstauflösung: dann Block 3 aus Sudo-Sammlung (truncate + logrotate force). Gelernt: 10,5 GiB → 115 KB in 2h ohne manuellen Eingriff auf Basti's System.
- **Check `os.access(path, os.W_OK)` before reporting a deletable item.**
- **`f3probe --destructive` requires sudo + real terminal** — `sudo -S` blocked by
  Hermes. Use `pty=True` or `f3write`/`f3read` on mounted volume. See
  `references/fake-storage-validation.md`.

Full 13-item pitfalls list (incl. `disk.percent` AttributeError, f-string backtick
bug, `err_msg()` helper, complex multi-line edits) in `safety-patterns.md`.

## Full System Audit Lifecycle (4-Phase Pattern)

> **Gelernt 2026-07-17:** Full System Audit auf Basti's Workstation — logrotate,
> Video-/Downloads-Archiv, .steampath-Cleanup, AGENTS.md-Drift. 22.7 GB Recovery,
> 4 Cron-Wächter installiert.

Dieses Pattern beschreibt den **vollständigen Audit-Lifecycle** von der
Ist-Zustandserfassung bis zur dauerhaften Überwachung. Es kombiniert die
Log-Diagnose aus "Log File Runaway Diagnosis" mit disk retention cleanup aus
"Disk Analysis Drill-Down Hierarchy" und fügt Systematisierung, Zukunftssicherung
und Langzeitüberwachung hinzu.

### Wann dieses Pattern anwenden

- User sagt: "mach mal einen System-Audit" / "räum auf" / "wie voll ist die Platte?"
- Wiederkehrende Symptome: Logs wachsen unkontrolliert, Disk schwankt zwischen
  82-88%, cron-Jobs scheitern still
- Nach grösseren Updates, Filesystem-Restrukturen oder Cluster-Migrationen
- Monatlicher/vierteljährlicher "deep clean"

### 🔍 Phase 1: Pre-Exec State Capture (Read-Only)

Vor jeder Änderung: **systematischen Baseline-Capture** fahren. Kein Tool-Call,
der schreibt, bevor die Baseline dokumentiert ist.

```bash
# Capture 1: Disk-Baseline
df -h / /mnt/DATA
du -sh /var/log/syslog*
journalctl --disk-usage

# Capture 2: Service-Health
systemctl is-active logrotate.service
systemctl is-enabled ollama

# Capture 3: Known-Drift-Agenda
# - AGENTS.md stale claims prüfen ("disabled+inactive", "last recorded state")
# - Mnemosyne high-importance (> 0.85) Items der letzten 30 Tage
# - Dateien > 1 GB die archiviert werden könnten: find $path -type f -size +1G
```

**Pitfall — Mnemosyne-Referenced-File-Halluzination (Pitfall #42):**
Wenn Mnemosyne-Recall einen Pfad referenziert (z.B.
`~/docs/system/quality-gates/daily-addendum-gate.sh`), IMMER vor dem ersten
Tool-Call mit `ls -la` verifizieren ob das File existiert. Mnemosyne merkt sich
dass **über** ein File gesprochen wurde, nicht dass es existiert.

**Pitfall — Audit-Scope-Creep (Pitfall #41):** Vor jedem Deep-Audit mit
Domain-Scope: (1) Welche Schwester-Domänen? (2) Mnemosyne high-importance
der letzten 30 Tage? (3) Open Issues in `~/.hermes/docus/reports/`?

**Pitfall — Bash `grep -c` Multi-Line-Output:** Wenn `grep -c` mehrere Files
matched oder stderr in stdout leakt, kommt die Ausgabe als "N\nM\n" returned
statt "N". Fix: immer `grep -c ... | head -1 | tr -d ' \n'` mit
`HITS=${HITS:-0}`-Fallback wrappen. Siehe `references/bash-grep-c-pitfall.md`.

### 🛠️ Phase 2: Task Execution (Sortiert nach Risiko)

Nach Baseline: **Tasks priorisieren und ausführen** — Reihenfolge:

| Stufe | Typ | Beispiele | Risk |
|---|---|---|---|
| 1 | Disk-Rescue (höchste Prio) | syslog truncate, logrotate force, journal vacuum | 🟢 |
| 2 | Archivierung (grosse statische Files) | Videos nach `/mnt/DATA/_Archives/`, Downloads tar.gz | 🟢 |
| 3 | Stale-Entities entfernen | dangling symlinks, .bak-Files, tote Service-Files | 🟡 |
| 4 | Drift-Korrekturen | AGENTS.md, CLAUDE.md stale claims | 🟢 |

**Pro Task: Queen-Briefing-Pattern mit 3 Punkten:**
```
### <Task-Name>
- **Ziel:** <was passieren soll in einem Satz>
- **Aktion:** <konkreter Befehl / Tool-Call>
- **Verify:** <wie nach Prüfen ob geklappt> → erwartet: <Soll-Ergebnis>
```

**Vorher/Nachher dokumentieren.** Grössen in Bytes, nicht nur human-readable.

### 🕒 Phase 3: Future-Proofing via Cron Watchdogs

Nach akuten Problemen: **Cron-Jobs für automatisierte Überwachung** einrichten.

**Checkliste:**

| Watchdog | Schedule | Schwellwert | Telegram | Script |
|---|---|---|---|---|
| disk-space-monitor | Daily 22:00 | / > 85% | ✅ | `~/50-System/bin/disk-space-monitor.sh` |
| logrotate-health | Weekly So 04:00 | syslog > 1GB oder Service abnormal | ✅ | `~/50-System/bin/logrotate-health.sh` |
| agents-md-drift | Weekly So 22:30 | "disabled+inactive"/"last recorded state" | ✅ | `~/50-System/bin/agents-md-drift-check.sh` |
| nextcloud-log-rotation | Alle 2h | > 2MB (silent truncate) | ❌ | `~/50-System/bin/nextcloud-log-rotation.sh` |

**Telegram-Notify-Pattern (aus Cron-Skripten):** `source $HOME/.hermes/.env`
+ `curl` zur Telegram-API. Siehe `references/telegram-cron-notify-pattern.md`.
❌ NICHT `hermes send_message` — das Subcommand existiert nicht.

**Log-Rotation der Watchdog-Logs selbst:** Jedes Watchdog-Script soll seine
eigenen Logs bei > 1MB rotieren (tail + gzip + truncate).

### ✅ Phase 4: Verify & Final Report

Nach Cron-Installation: **JEDES Script einmal ausführen.**

**Verify-Checkliste:**
```
1. Sanity-Test jedes Watchdog-Scripts: bash ./script.sh
2. Log-File prüfen: cat ~/logs/<script>.log  → hat Output? Exit-Code 0?
3. Crontab-Inspect: crontab -l | grep <script> → Zeile da? Pfad existiert?
4. Telegram-Test (einmalig): source $HOME/.hermes/.env
   && curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage"
   -d "chat_id=${TELEGRAM_HOME_CHANNEL}" -d "text=🟢 Test"
   → {"ok":true} in Response?
5. Final Report: Pre/Post-Vergleich + offene Items + Memory-Updates
```

**Report-Format:** `~/.hermes/docus/audits/<YYYY-MM-DD>-full-audit-report.md`
mit Pre/Post-Statistik, Cron-Liste, offenen Items.

## External Tools

| Tool                                                | What it does                    | When to use                                |
|-----------------------------------------------------|---------------------------------|--------------------------------------------|
| `bleachbit`                                         | GUI/CLI system cleaner          | User wants "CCleaner for Linux" out of box |
| `stacer`                                            | Qt system monitor + cleaner     | User wants GUI with CPU/RAM/Disk tabs      |
| `ncdu` / `baobab`                                   | Interactive disk analyzer       | TUI (`ncdu`) or GUI tree-map (`baobab`)    |
| `rmlint`                                            | Duplicate finder + symlinks     | Duplicate media/libraries                  |
| `f3`                                                | f3probe/f3write/f3read          | Fake SD/USB — see `references/fake-storage-validation.md` |
| `apt autoremove` / `apt clean`                      | Orphan packages / APT cache     | After upgrades / always first              |
| `flatpak uninstall --unused` / `snap list --all`    | Remove unused runtimes/revisions| Flatpak / Snap space-hungry                 |

## Hermes Integration

For recurring cleanup, register as a cron skill:

```bash
hermes cron create "0 8 * * 0" \
  "Lade linux-system-maintenance Skill. Scanne mit Dry-Run. \
   Wenn > 5 GB gefunden, sende Zusammenfassung und frage nach Clean." \
  --skill linux-system-maintenance
```

For deterministic, fixed-threshold cleanups that don't need an LLM, use
`--no-agent` mode with a stdlib script (see `safety-patterns.md`).

## Extended Scanners (Post-MVP)

Hash-based duplicate detection (group by size → parallel hash) and top-N large-file
scanning with depth-limit. Skip known-huge dirs (`node_modules`, `__pycache__`,
`proc`, `sys`, `dev`). Full code in `references/disk-analysis.md`.

## Gaming Storage Toolkit

For users with large Steam/Game libraries on external drives, a companion toolkit
(`steam_inventory.py`, `steam_archive.py`, `data_cleanup.py`) handles backups,
installations, and Recordings/ separately. Mount externals by UUID but symlink
`/mnt/DATA`. `.Trash-1000/` on externals can hold **80+ GB**. Full guide in
`cleanup-procedures.md`.

## Firmware & Hardware Security Audits

Interpret HSI levels from `fwupdmgr security`: `Linux Swap: Fail` → ZRAM;
`Suspend To RAM: Fail` → s2idle; `Linux Kernel Verification: Fail` → usually
harmless (taint code); `Encrypted RAM: Fail` → hardware limitation. Goal: HSI:3
on consumer hardware. Full playbook: `references/security-hardening.md`.

## Home Directory Top-Level File Classification („Home-Scout")

When the user asks for a cleanup audit, home inventory, or file classification
of `~/` top-level files — use the **Home-Scout Protocol** in
`references/home-scout-classification.md`.

### Quick-start

```bash
# 1. Scan
find /home/bratan -maxdepth 1 -type f -printf '%p\t%s\t%TY-%Tm-%Td %TH:%TM\n' | sort

# 2. Pro File: Kategorie (Bericht/Playbook/Test/...), Domäne, Eigentümer, Priorität, Status
# 3. Cross-Reference: Duplikate, Ghost-Files, Test-Cluster identifizieren
# 4. Report: 5-Section-Format (Inventar → Quick-Wins → Author-Map → Domain-Zuordnung → Orphans)
# 5. EXPLIZIT deklarieren: „Keine Moves ausgeführt — nur Analyse."
```

### Key signals that trigger this protocol

- User asks for a „cleanup report", „home scout", or „file inventory"
- Unexplained disk usage in `~/` with no obvious culprit
- Multiple test/cache files accumulating in the home root
- Preparing for a `NAVIGATION.md` or `DESCRIPTION.md` update

### Pitfalls

- **Never recurse** into subdirectories — that's a separate deep-scan task.
- **Don't touch system config** (`.bashrc`, `.gitconfig`, `.profile`, etc.) — mark as
  legitimate, don't recommend for deletion.
- **Read-only.** Report only — never execute removes during the scan.
- **Author attribution from headers.** Don't guess — check `head -5` for "Author:",
  "Bearbeitet von:", or tool-generated JSON keys.
- **Ghost-file detection** always: empty-content files, whitespace names,
  root-owned files in `~/`, HTML-fail pages saved as binary names.

## Related System Skills (sibling)

| Skill | Covers |
|-------|--------|
| `linux-system/waydroid-setup` | Android container (Waydroid) — binder_linux, NVIDIA+Wayland quirks, LXC management, network inside Android guest |
| `linux-system/linux-wifi-setup` | WLAN activation — rfkill, nmcli, sudo-free via PolicyKit/D-Bus, dual-stack LAN+WLAN routing |

## References

- `references/cleanup-procedures.md` — rc package purge ordering, kernel cleanup
  rule, steam-installer workaround, log/cache audit, mail client detection,
  gaming toolkit, firmware audit decision tree.
- `references/disk-analysis.md` — Manual inspection workflow (health check,
  package audit, log/cache audit), duplicate finder + large-files scanner code,
  worked example (30 GB reclaimed, 2026-06-03).
- `references/safety-patterns.md` — 13-item pitfalls list, CLI UX pattern, JSON
  output workaround, Telegram pattern, agent + `no_agent=True` cron, multi-tool
  testing pattern.
- `references/system-inspection-2026-06-03.md` — Full scan + cleanup on Zorin OS
  18.1 gaming desktop. Workarounds discovered.
- `references/cli-tool-stdlib-pattern.md` — Stdlib-only CLI architecture (no
  rich/psutil). Used for sysdoctor, greysync, gmail-organizer.
- `references/gmail-cron-pattern.md` / `references/gmail-imap-cleanup.md` —
  Gmail cleanup via no_agent cron + imaplib stdlib (connection, no-reply
  patterns, Evolution detection).
- `references/yuno-cleaner-implementation.md` — yuno-cleaner rich-TUI
  architecture, multi-module structure.
- `references/log-file-diagnosis.md` — 7-Phasen-Methodik für read-only Logfile-Runaway-Diagnose: awk-Prozess-Byte-Counting, logrotate Health-Check inkl. ConditionACPower und Rotation-Historie im syslog, Root-Cause-Extension/Service/Kernel, P0/P1/P2-Bewertung. Ausgearbeitetes Beispiel: 6,4 GB syslog durch gnome-shell-Extension-Spam mit 3 übersprungenen Rotationen.
- `references/security-hardening.md` / `references/security-audit-workflow.md` —
  fwupd HSI audit + desktop security audit (services, ports, UFW localhost).
- `references/fake-storage-validation.md` — SD/USB fake-capacity detection with
  f3, sudo+terminal workaround, fake-card indicators.
- `references/home-scout-classification.md` — Home Directory Top-Level File Classification
  Protocol: Kategoriematrix, Ghost-/Duplicate-Erkennung, Autoren-Map, 5-Section-Report-Format.
- `references/fwupd-hsi-power-mgmt-2026-06-08.md` — fwupd HSI event-based
  behavior, s2idle, GNOME gsd-power workaround, swap strategies.
- `references/telegram-cron-notify-pattern.md` — **NEU 2026-07-17:** Telegram-Notification
  aus Bash-Cron-Jobs: `source .env` + `curl`, NICHT `hermes send_message`.
  Mit Fallback-Guard, Token-Quellen und Anti-Patterns.
- `references/bash-grep-c-pitfall.md` — **NEU 2026-07-17:** `grep -c` Multi-Line-Integer-
  Comparison Bug und Fix (head-1 + tr + Fallback). Bash-Python-Entscheidungsmatrix.
- `references/system-audit-2026-07-17.md` — **NEU 2026-07-17:** Vollständiger Full-System-
  Audit (22.7 GB Recovery, 4 Cron-Wächter, logrotate, Video/Downloads-Archiv), Report
  im 5-Section-Format mit Pre/Post-Statistik.
