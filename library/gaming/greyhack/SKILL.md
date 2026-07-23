---
name: greyhack
description: "Use when user asks for GreyScript language reference, GreyHack scripting patterns, three-layer mental model, GreyScript deployment. NOT for non-GreyHack games or other MMO scripting languages. GreyHack MMO scripting — GreyScript language reference and arsenal."
version: 2.3.0
author: Hermes Agent (curator consolidation)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - gaming
    - greyhack
    - miniscript
    - scripting
    - hacking-sim
    - pattern-governance
    lane: worker-flash
    reasoning_effort: high
changelog:
  - version: 2.3.0
    date: 2026-07-22
    changes: |
      Post-PR-#66 Update: Pattern-Governance-Architektur, Build-Status nach PR #63/#66/#67/#68/#77,
      xmem Branch-Merge-Gap entfernt, Wiki Cross-Link Strategy. 3 neue References:
      pattern-governance.md, build-status-post-pr-66.md, wiki-cross-link-strategy.md.
      Live-Audit am 2026-07-22 von Bastis Working-Tree /home/bratan/ZCodeProject/greyscripts.
  - version: 2.2.0
    date: 2026-07-15
    changes: |
      Curator consolidation: alle 50+ Bug-Patterns in known-bugs.md, 56+ Pitfalls in greyscript-language.md,
      alle 12 YUNO-Versions dokumentiert, Deployment-Workflow-Large-Files neu.
trigger_keywords: ['greyscript', 'greyhack', 'scripting', 'language', 'reference']
keywords: ['greyscript', 'greyhack', 'scripting', 'language', 'reference']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['greyhack-greyscript', 'greyhack-sandbox', 'greyhack-hermes-api']
---



# GreyHack — GreyScript Arsenal

Complete GreyHack MMO scripting guide: language reference, API objects, exploit workflows, toolset design, community script auditing, deployment, and Hermes co-pilot.

## Three-Layer Mental Model
1. **Sprachebene** — variables, lists, strings, maps, functions, conditions, loops
2. **Objektebene** — Shell, Computer, File, Router, Crypto, Metaxploit, AptClient
3. **Werkzeugebene** — portscan, routerinfo, smtp_enum, wifi_crack, metaxploit workflow

## Quick Links

| Topic | Reference |
|-------|-----------|
| **Fileserver Setup** | → `references/fileserver-setup.md` |
| **Large File Deployment** | → `references/deployment-workflow-large-files.md` |
| **DB Schema** | → `references/db-schema.md` |
| **//command: Marker** | → `references/config-command-marker.md` |
| **CodeEditor Workflow** | → `references/codeeditor-direct-workflow.md` |
| **Multi-Agent Bug Sweep** | → `references/multi-agent-bug-sweep-2026-07-07.md` |
| **Starter-Kit Pipeline** | → `references/starter-kit-tool-pipeline.md` |
| **Pattern-Governance** | → `references/pattern-governance.md` (NEU 2026-07-22) |
| **Build Status post-PR-66** | → `references/build-status-post-pr-66.md` (NEU 2026-07-22) |
| **Wiki Cross-Links** | → `references/wiki-cross-link-strategy.md` (NEU 2026-07-22) |
| **YUNO Versions** | → `references/yuno-project-versions.md` |
| **Language Pitfalls** | → `references/greyscript-language.md` |
| **API Reference** | → `references/greyscript-api-reference.md` |
| **Audit Patterns** | → `references/greyscript-audit.md` |
| **Known Bugs** | → `references/known-bugs.md` |
| **DB Internal FS Audit** | → `references/db-internal-filesystem-audit.md` |

## Storage & Cleanup

GreyHack hat zwei orthogonale "Platz"-Probleme:

| Pfad | Was | Wie groß |
|------|-----|----------|
| `Grey Hack/yuno-tools/*.src` | **Template-Sammlung auf Linux-Disk** | ~96 KB über 31 Scripts |
| `Grey Hack/Grey Hack_Data/GreyHackDB.db` → `Computer.FileSystem` JSON | **In-Game-Storage** des Player-PCs | Limit durch HDD-Hardware, z.B. 350 MB |

**DB Schema & Analysis:**
- → `references/db-schema.md` — LIVE Schema (V0.9.6771-beta)
- → `references/db-state-analysis.md` — State-Analyse (Spieler, Computer, Hardware, Missionen)
- → `references/db-hash-delta-forensics.md` — Hash-Delta-Forensik (Watchdog)
- → `references/db-schema-analysis.md` — Alle GreyHack-Tabellen (Map, WebPages, Logs, Computer, PlayerConns)

**Kritisch:**
- → `references/config-command-marker.md` — `//command:` Marker PFLICHT für Source-Scripts
- → `references/config-deployment-db-injection.md` — Config/-Deployment via DB-Injection
- → `references/storage-consolidation.md` — Script-Konsolidierung + All-in-One yuno.src Pattern
- → `references/in-game-db-edit.md` — GreyHackDB.db SQLite-Workflow mit Backup-Pattern + Whitelist

## Deployment-Methoden (sortiert nach Präferenz)

| # | Methode | Beschreibung | Wann |
|---|---------|-------------|------|
| 1 | **CodeEditor + Copy-Paste** | Browser/Fileserver öffnen, markieren, in CodeEditor pasten | Files <30 KB, Bastis Standard |
| 2 | **pc.wget()** | Ein GreyScript-Befehl in der Shell → `references/deployment-workflow-large-files.md` | Files <100 KB, Game auf gleicher Maschine |
| 3 | **DB-Injection** | `INSERT INTO Files` direkt in GreyHackDB.db | Files >30 KB, große Dateien |
| 4 | **CodeEditor + Chunking** | File in 2-3 Teile splitten, nacheinander pasten | Wenn 1-3 nicht gehen |

**WICHTIG:** Bei Basti IMMER mit Whitelist arbeiten ("da sind System-Programme wie apt drin"). Niemals blind `rm /bin/*` im Spiel.

## Critical Language Pitfalls

→ `references/greyscript-language.md` — Full pitfall catalog (56+ categories)

**Top 10:**
- **Strings:** double quotes only — single quotes cause silent syntax failures
- **`indexOf` returns `-1` when not found** — NOT `null`
- **`delete`/`touch()` return `""` on success** — NOT `1`, NOT `null`
- **`0` is truthy** — use `!= 0` not `if result`
- **Negative indexing:** `params[^0]` (caret) does NOT WORK — use `params[params.len - 1]`
- **`for x in map` returns KEYS** — use `for k in map.indexes; v = map[k]`
- **One-line `if ... then BODY end if` is unsafe** — use multi-line form
- **Cache `get_shell.host_computer`** — `pc = shell.host_computer` once
- **`globals.x` does NOT make `x` locally available** — use direct local assignment
- **Bare read of undefined module-level global crashes** — `if not globals.hasIndex("h") then globals["h"] = {} end if`
- **`.strip()` and `.trim()` do NOT exist** — crashes at runtime, use manual trim-loop (NP-79 in `references/known-bugs.md`)

## API Objects

→ `references/greyscript-api-reference.md` — Complete API (all objects, methods, return types, verified 2026-06-27)

### Key Objects Quick Reference

| Object | Key Methods | Source |
|--------|-------------|--------|
| `Shell` | `build()`, `launch()`, `host_computer`, `connect_service()`, `scp()`, `ping()` | `get_shell` |
| `Computer` | `File()`, `get_ports`, `get_name`, `public_ip`, `local_ip`, `is_network_active`, `create_folder()`, `touch()` | `shell.host_computer` |
| `File` | `get_content`, `is_binary`, `is_folder`, `name`, `path`, `size`, `permissions`, `get_files`, `get_folders`, `parent`, `delete`, `chmod()`, `copy()`, `move()`, `rename()` | `pc.File(path)` |
| `Port` | `port_number`, `is_closed`, `get_lan_ip` | `pc.get_ports` |
| `Router` | `used_ports`, `get_lan()`, `get_public_ip()`, `port_info()` | `get_router()` |
| `Crypto` | `smtp_user_list()`, `crack_zip()`, `decrypt()` | `include_lib("/lib/crypto.so")` |
| `Metaxploit` | `load()`, `net_use()`, `scan()`, `scan_address()`, `overflow()`, `rshell_client`, `rshell_server`, `sniffer` | `include_lib("/lib/metaxploit.so")` |
| `MetaLib` | `overflow()`, `version`, `lib_name`, `is_patched`, `debug_tools()` | `metax.load()` or `net.dump_lib` |
| `NetSession` | `dump_lib`, `get_num_users`, `is_any_active_user` | `metax.net_use()` |
| `AptClient` | `install()`, `remove()`, `update()` | `include_lib("/lib/aptclient.so")` |
| `BankAccount` | `account`, `balance`, `wireMoney()` | `pc.BankAccounts[i]` |
| `MailAccount` | `address`, `password` | `pc.MailAccounts[i]` |

⚠️ **Port-Properties in Mock-Env:** `pc.get_ports()` kann Maps ohne alle Keys zurückgeben → 4-stufige Guard-Kette in `references/mock-env-port-guard.md`

## Metaxploit Workflow (6 Steps)

1. `meta = include_lib("/lib/metaxploit.so")`
2. `lib = meta.load(path)` (local) or `net = meta.net_use(ip, port); lib = net.dump_lib` (remote)
3. `print(lib.lib_name); print(lib.version)`
4. `addrs = meta.scan(lib)`
5. For each `addr`: `info = meta.scan_address(lib, addr)`
6. `result = lib.overflow(addr, unsecValue)` — **always typeof() before processing**

→ `references/in-game-hacking-workflow.md` — Router → Metaxploit → SSH → File Access → Decipher → Money

## Community Script Auditing

→ `references/greyscript-audit.md` — Full audit pattern catalog
→ `references/known-bugs.md` — NP-18–NP-67 bug pattern list + known persistent bugs

### Common Audit Patterns (Top 12)

| # | Pattern | Fix |
|---|---------|-----|
| 1 | `\n` in strings, or `"char(10)"` literal | Replace with `char(10)` (function call, no quotes) |
| 2 | `self` param on map methods | Remove explicit `self` |
| 3 | `indexOf` compared to `null` | Compare to `-1` |
| 4 | `get_content or ""` | Null-check instead |
| 5 | `shell.build() == 1` | Use `typeof == "string"` |
| 6 | `File.chmod(600)` integer | Use `"o-rwx"` string |
| 7 | `delete == 1` | Use `== ""` |
| 8 | Silent catch blocks | Add logging |
| 9 | `range(0, len-1)` empty list | Guard against `range(0, -1)` |
| 10 | `include_lib` no null-check | Add null-check after |
| 11 | `HTTP.Request()` usage | Does NOT exist in Vanilla GreyScript |
| 12 | Mixed API underscore styles | Use no-underscore: `getcontent`, `setcontent` |

## Build & Deployment

### greybel-js Installer (Preferred)
```bash
npm install -g greybel-js
npx greybel build master_installer.src --installer --uglify --ingame-directory /home/Bratan/bin
```

### Phase A — Direct DB Injection (Source Tools → In-Game)
For deploying individual `//command:`-style source tools (not uglified installers) directly into the game's Config/ folder via GreyHackDB SQLite injection:

→ `scripts/greyhack-deploy-tools.py` — **Generalized deploy script**: backup, Files/FileSystem injection, verification. Pass one or more `.src` files:
```bash
python3 scripts/greyhack-deploy-tools.py tools/yuno_bootstrap.src tools/yuno_nscan.src
```
**Size Limit:** GreyHack auto-loads `//command:` scripts via the CodeEditor up to ~12 KB. Files up to ~50 KB work via Ctrl+O → Build → Shell. The script handles both ranges — no size constraint on the DB side.

**Deploy Pipeline (used 2026-07-15 for Phase A):**
- Reads source files, verifies `//command:` header
- Creates timestamped backup of GreyHackDB.db
- INSERT/UPDATE in Files table as `Config/<name>.src` (relative path)
- Walks FileSystem JSON to `/home/<player>/Config/`, adds matching file entries
- Commits with integrity_check

**Player config:** Edit `_DEFAULT_PLAYER` at top of script, or set `GREYHACK_PLAYER` env var. Default: `gregor`.

→ `references/db-deployment-injection.md` — Theory: two-step Files + FileSystem injection
→ `references/config-deployment-db-injection.md` — SQL-level manual workflow
→ `references/build-troubleshooting.md` — Detailed build troubleshooting, import path rules, CI pipeline patterns

### Build & Deploy Scripts
- `/home/bratan/bin/greyhack-deploy` — builds all tools and fixes import paths → `~/greyhack-tools/deploy/`
- `/home/bratan/bin/greyhack-build` — builds all/single tools → `~/greyhack-tools/bin/`
- Fileserver: `cd ~/greyhack-tools && python3 ~/bin/temp_fileserver.py &` (Port 8765)

### Build Success Rate (post-PR-#66, 2026-07-22)

✅ **Pattern-Governance-Architektur** aktiv (PR #66, gemerged 2026-07-21):
12 verified-Patterns aus `src/core/*` extrahiert nach `patterns/{build,files,typing,net,router,cli}/`,
alle mit Unterstrich-API (`get_shell`/`host_computer`, `get_content`, `get_ports`),
Score ≥90/100. CI-Job `pattern-governance` mit `make check-all` als Single-Source-of-Truth.

✅ **PR #67** (gemerged 2026-07-21): Batch 2 mit 4 weiteren verified-Patterns
+ 6 Real-Bug-Fixes aus adversarialem Review.

✅ **PR #68** (gemerged 2026-07-21): harden recon reporting and governance
checks — pytest 9 passed, make check-all OK, ci-build.sh 83/83 OK.

✅ **PR #77** (gemerged 2026-07-22): initial wiki population - 65 Pages,
0 broken Cross-Links.

✅ **PR #63** (gemerged 2026-07-15): feat(starter) standalone tools +
controlcenter UI layout — yuno_bootstrap, yuno_localrecon, yuno_nscan,
setup, portscan, uicore, configcore, controlcenter. **In-Game Start-Chain
verfügbar:** `yuno_bootstrap → yuno_localrecon → yuno_nscan → hardening_audit → controlcenter/yuno_v6`.

✅ **xmem-Caveat entfernt** (gefixt zwischen 14.07. und 22.07.):
`~/greyhack-tools/xmem/` enthält `xmem.src` (33 KB) + `README.md`.
Branch-Merge-Gap ist geheilt.

### Branch-Stand 2026-07-22

- **`main`**: enthält PR #66, #67, #68, #77 (alle merged)
- **`develop`**: enthält PR #63 (Starter-Kit, merged 2026-07-15)
- **`modernize/python-and-guards`** (lokal aktiv, kein PR): 3 frische Commits
  - `1717812` — `_LIBCORE_LOADED` Import-Guards in 7 Modulen
  - `5bebfe8` — `_extract.py` als echte CLI + Counter-Fix
  - `9dab76c` — `greysync.py` argparse subparsers + scp-Port-Fix (`-P` statt `-p`)

→ `references/build-status-post-pr-66.md` für Detail-Build-Tabelle.

→ `references/bug-fix-history.md` — Fix history, auto-fixers, pre-scan patterns

### Pitfall-Update 2026-07-22

**Lesson (gefixt):** Der `feature/...`-Branch-Workflow erzeugt Branch-Merge-Gaps.
Der xmem-Case zeigt dass "builds on branch" ≠ "builds on develop" — der Gap kann
9+ Tage unbemerkt persistieren. **Pattern bleibt:** `git branch --show-current` +
Listing der submodule-relevanten Verzeichnisse vor jeder Build-Status-Tabelle.

**Neue Lesson:** Wiki-Initial mit 65 Pages ist Wiki-Architecture, nicht Doku-Append.
Bei Wiki-Stale-Check zukünftig beide Layer (Vault-Notes + Repo-Wiki) im Auge behalten.

## Pattern-Governance (NEU post-PR-#66)

Seit PR #66 (gemerged 2026-07-21) hat das Repo eine **Pattern-Governance-
Architektur** als additive Schicht. 12 verified-Patterns (Score ≥90/100)
leben unter `patterns/{build,files,typing,net,router,cli}/`, alle mit
Unterstrich-API-Konvention (`get_shell`/`host_computer`, `get_content`).

**CI-Single-Source-of-Truth:** `make check-all` (5 Checks: doc-links,
meta, naming, pattern-layout, verified-index).

→ `references/pattern-governance.md` für die volle Architektur, Score-System,
Promotion-Workflow, MIGRATION-MAP und Known-Warnings.

**Auswirkung auf Skill:** "Wo neue Pattern hinzufügen?" wird via Promotion-
Workflow beantwortet, nicht durch Copy-Paste aus altem Code.

## In-Game Start-Chain (post-PR-#63)

Verfügbar nach PR #63 (gemerged 2026-07-15):

```
yuno_bootstrap        → First-Run Layout Check + Tool-Chain Anzeige
yuno_localrecon       → Host-Inventur (Users, Libs, Ports, Bin)
yuno_nscan            → Portscan IP/LAN/local mit Mock-safe Port-Property-Guards
hardening_audit       → File-Permissions + SUID-Scan
controlcenter         → Terminal-Hauptmenü, Themes, key=value-Persistenz
  oder yuno_v6        → Full-Feature-Frameworks (Theme, Macros, multi-instance)
```

## Multi-Agent Bug-Scan Sweep Workflow (2026-07-07)

**Trigger:** User asks "fix all bugs" / "schwarm drüber" / "auto-fix sweep" / "welle N go"

→ `references/multi-agent-bug-sweep-2026-07-07.md` — **Full workflow mit 5-Phasen-Pattern** (proven 2026-07-07, 2 PRs #56+#57, 41→66/66 OK)

**5-Phasen-Pattern (Quick Summary):**
1. **Phase 0 — Inventur** — `git ls-files`, Static-Scan (alle Files!), CI-Build, 5-Kategorien-Klassifizierung
2. **Phase 1 — Library-Filter** — Pflicht-Filter für "missing //command: marker" Sweeps
3. **Phase 2 — Schwarm-Dispatch** — NON-OVERLAPPING Sub-Agent-Scopes + Sentinel-Token
4. **Phase 3 — Master-Verify** — `git status`, `ci-build.sh`, Sentinel-Check, Backup-Check
5. **Phase 4 — Commit + Push + PR** — Branch-Checkout + PR-Body mit Pattern-Tabelle

**5-Kategorien-Build-Fail-Klassifizierung:** Pattern-bug | Import-resolution | API-not-found | Type-mismatch | Mock-env-only

**6 Sub-Agent-Fallen:** Coverage-Gap | Filter zu aggressiv | Report-Truncation | Race-Condition | Library-Filter zu eng | Fehldiagnose

## Cron Bug-Fixer Configuration

### Truncation Prevention (CRITICAL)
→ `references/cron-bug-fixer-config.md` — Batch limit + State tracking + Filter pipeline

### CI-Bug NP-99 (2026-07-07) — ((BUILT++)) Exit-Code-Falle
→ `references/ci-bug-np-99.md` — Pre-increment (`++var`) mit `|| true` Wrapper unter `set -euo pipefail`

### Cron-Mode Blocker-Patterns (2026-07-06)
→ `references/cron-mode-blocker-patterns.md` — BLOCKED: `execute_code`, heredoc, `python3 -c`, `find -delete`, `xargs rm`, root-path `rm`. Workaround: `write_file` → `terminal python3 /tmp/script.py`

→ `references/db-watchdog-cron.md` — Vollständiger Workflow mit State-File-Recovery und Symlink-Pitfalls

## GreyHack Terminal

Das GreyHack-Terminal ist **kein GreyScript-Interpreter**. Es ist ein Bash-ähnliches Terminal im Spiel.

**Das Terminal selbst hat KEIN wget/curl/http_get Kommando.** Das bezieht sich auf das Bash-Terminal, nicht auf GreyScript-Funktionen.

**ABER: `pc.wget(url, dst)` existiert als GreyScript-Funktion im Spiel!** (community-discovered, nicht offiziell dokumentiert). → `references/fileserver-setup.md`

**NICHT VERWECHSELN:**
```
# Terminal — ❌ geht nicht
wget http://192.168.178.92:8765/tool.src

# GreyScript im CodeEditor oder per paste — ✅ funktioniert
pc.wget("http://192.168.178.92:8765/tool.src", "/tmp/tool.src")
```

## In-Game Deployment Methods

**A: CodeEditor** — CodeEditor öffnen → GreyScript pasten → Save → Build → Run
**B: Terminal + nano + shell.build** — `nano /home/Bratan/bin/<name>.src` → `shell.build(...)` → Run
**C: Fileserver + Copy-Paste** — Host fileserver → Browser → Copy → CodeEditor Paste
**D: greybel import** — `greybel import <file.src> -pt 8332 -id "/home/Bratan"`

## Deployment-Dokumentation erstellen

→ `references/deployment-doc-template.md` — Multi-Source Research + Template (3 Quellen kombinieren: Build-Artefakte + Existierende Doku + DB-Archäologie)

**Dokument-Struktur-Vorlage:** Warum KEIN <common-but-wrong-assumption> | Deployment Workflow (N Schritte) | Module & Command-Übersicht | Build-Schritte (Host) | Troubleshooting | Quick-Reference-Card

## GitHub + GreyHack Automation

```bash
python3 scripts/hermes-automation.py issue --title "tool: routerinfo" --label "new tool" --milestone v0.3.0
python3 scripts/hermes-automation.py branch --issue 5 --name feature/routerinfo
python3 scripts/hermes-automation.py build --file tools/routerinfo.src --verify
python3 scripts/hermes-automation.py pr --issue 5 --title "feat: routerinfo Closes #5"
```

### GitHub Issue Sync Pitfalls
- **Batch into a single Sammel-Issue**, not N individual issues
- **Custom labels are blocked** in maintainer repos — use only standard labels
- **Shell escaping**: Backticks in `gh pr comment --body "..."` get executed
- **Subagent rate limits**: Multi-agent orchestration may hit HTTP 429

## Hive Lord / Queen — In-Game Teaching Sessions

| Wer | Rolle | Kurz-Code |
|-----|-------|-----------|
| **Basti** | Hive Lord — befehligt den Bienenstock | `HL` / `Lord` |
| **Yuno (Queen)** | Bienenkönigin — steuert den Schwarm | `Q` |
| Sub-Agenten | Workers (Drones) — führen Aufgaben aus | `W` |

**Q-Command Codes:** `Q GO` (Start), `Q NEXT`, `Q WAIT`, `Q HOLD`, `Q ACK`, `Q DONE`, `Q ERR BUILDFAIL/CONNECT/CRASH/CONFUSED`
**Actions:** `Q SCAN <IP>`, `Q CONNECT <IP>`, `Q TOOL <name>`, `Q FILESERVER`, `Q BUILD <file>`

Tutorial-Docs: `~/docs/greyhack-tutorial/01-starter-cheatsheet.md`, `02-first-tool-test.md`, `03-quick-comm-codes.md`

## is_folder vs is_binary — Definitive Answer

`is_folder` IS valid GreyScript but **unreliable in practice**. Safer pattern:

```greyscript
if f.is_binary then
  // It's a file
else
  // It's a directory (null-check first!)
end if
```

## Mock-Env Test-Workflow (greybel execute)

**Bevor du neue Tools ins Spiel jagst: lokal mit Mock-Env testen.** Das spart Game-Restarts und crashed keine echten NPCs.

```bash
# 1. Build check
npx greybel build /path/to/tool.src -u

# 2. Mit Mock-Env ausführen (Subcommand simulieren)
npx greybel execute /path/to/tool.src -p help --silent
npx greybel execute /path/to/tool.src -p scan 199.229.146.172 --silent
npx greybel execute /path/to/tool.src -p loot --silent

# 3. Mit Seed (für reproduzierbare Mock-Welten)
npx greybel execute /path/to/tool.src -s 12345 -p loot --silent
```

**Was Mock-Env hat:** Dummy-Computer mit IPs, NPCs, Ports (manche ohne alle Properties — siehe NP-68), basic `get_shell`, `File()`, `Crypto`. **Was NICHT:** echte `metaxploit.so`, echtes Internet, persistente Saves.

**Pitfalls:**
- → `references/mock-env-port-guard.md` — 4-stufige Guard-Kette für Mock-Env Ports
- `crypto.decipher()` funktioniert in Mock-Env mit eingebauter Mini-Wordlist
- `--silent` unterdrückt Progress-Bar-Meldungen

**Iterativer Loop:** Build → Execute → Read stderr/stdout → Patch → Repeat. Typische Crash-Quote beim ersten Run: 20-30%.

## YUNO Project

→ `references/yuno-project-versions.md` — **Full Version History & Feature Comparison**

| Version | Größe | Features | Verfügbar als |
|---------|-------|----------|---------------|
| **V1** | 17 KB | 7 Subcommands, early-exit dispatcher | `templates/yuno-all-in-one.src` |
| **V2** | 45 KB | 50+ Commands, interactive shell | `~/docs/system/greyhack-yuno-v2-2026-07-03.md` |
| **V3** | 52 KB | V2 + Theme-System + Macro-System + getyuno | `~/docs/system/greyhack-yuno-v3-2026-07-03.md` |
| **V5** | ~66 KB | P0-sauber, 50+ Commands, CI-grün, ✅ **in-game getestet** | `~/greyhack-tools/yuno_v5_source.src` |
| **V6** | 78.2 KB Source → 45.7 KB Build | V5 + 6 neue Features: Disk-Persistenz, State Restore, Plugin Auto-Load, History Suggest, Sniffer, Coop. **⚠️ uglified, monolithisch** | Build only |
| **V6c** | 18 KB / 599 Z. | **Clean Minimal Edition** — lesbares, modulares GreyScript. Ideal als Startvorlage. | `templates/yuno-v6c.src` |

**Wann welche Version:**
- V1 (17 KB) — simple Tools ohne interactive shell
- V2 (45 KB) — 30+ Commands mit State-Management
- V3 (52 KB) — Full-Feature-Frameworks (Theme, Macros, multi-instance)
- V5 (~66 KB) — stabilen Daily-Driver (P0-sauber, ✅ **in-game getestet**)
- V6 (modular) — **Disk-Persistenz** + Cooperative Mode
- **V6c (18 KB)** — **lesbare, minimalistische Tools** — State + Top-10-Commands. Ideal als **Startvorlage**.

## References Index

### Storage & Cleanup
- `references/storage-consolidation.md` — Script-Konsolidierung (31 → 1), yuno.src Pattern
- `references/yuno-v6-architecture.md` — V6 architecture: 6 neue Features, Persistenz-Format, Config-PIPE-Schema
- `references/in-game-db-edit.md` — GreyHackDB.db SQLite-Edit für In-Game-Storage (Whitelist-Pflicht!)
- `references/db-state-analysis.md` — DB State-Analyse: Spieler-Status, Computer-Hardware, Filesysteme
- `templates/yuno-all-in-one.src` — V1 Working Template, 17 KB, 6 Subcommands, greybel-verified
- `~/docs/system/greyhack-storage-cleanup-2026-07-03.md` — Session-Doku mit Backup-Liste + Test-Results
- `~/docs/system/greyhack-yuno-v2-2026-07-03.md` — YUNO V2 architecture (45 KB interactive shell)
- `~/docs/system/greyhack-yuno-v3-2026-07-03.md` — YUNO V3 (52 KB, +Theme +Macros +getyuno)

### Core
- `references/greyscript-language.md` — Full language reference + 56 bug categories
- `references/greyscript-api-reference.md` — Complete API (verified 2026-06-27)
- `references/greyscript-audit.md` — Community script audit patterns
- `references/db-internal-filesystem-audit.md` — **NEW** (2026-07-15): Single-computer internal FS audit: Drift-Matrix zwischen Files-Tabelle (Content) und FileSystem-JSON-Tree. Python-Walker, Drift-Matrix-Builder, Soft-Limit (12288 B) Analyse, Befund-Kategorisierung. Aus der Biene B Viper-Phase-A Audit-Session.
- `references/in-game-hacking-workflow.md` — In-Game Hacking Workflow
- `references/ctf-mission-workflow.md` — CTF/Mission pattern
- `references/python-subprocess-patterns.md` — Python ↔ greybel-js integration
- `references/npc-database-patterns.md` — SQLite3 NPC-database
- `references/db-schema-analysis.md` — GreyHack DB Schema & Tabellen-Analyse
- `references/db-reconnaissance-pattern.md` — DB-driven Recon: Library-Hash-Einzigartigkeit, Bank/Mail-Domain-Cross-Reference, 4-Phasen-Modell
- `references/db-hash-delta-forensics.md` — Hash-Delta-Forensik: Clock-only-Tick, .dump+diff-Shortcut, Phantom-Cleanup
- `references/db-ip-cross-reference-deep-dive.md` — IP-Kreuzreferenz: BankAccounts, MailAccounts, Computer.ConfigOS, Passwords, Logs, Missions
- `scripts/greyhack-hitlist.py` — CLI-Scanner: SQLite-Queries, Scoring-Formel, Report-Generierung
- `references/auto-fix-pipeline.md` — Multi-Agent Auto-Fix Pipeline
- `references/mission-credential-protection.md` — Lebenszyklus von Mission-Credentials
- `references/db-watchdog-cron.md` — Cron-Betrieb des DB-Watchdogs: Workflow, Symlink-Management, Cron-Mode-Einschränkungen

### Bugs & Fixes
- `references/known-bugs.md` — All NP-18–NP-79 patterns + known persistent bugs + detection greps
- `references/bug-fix-history.md` — Fix logs, auto-fixers, pre-scan patterns, operational lessons
- `references/build-troubleshooting.md` — Build pipeline, import paths, CI, CLI mismatch
- `references/structural-repair-patterns.md` — Common structural bugs and fixes
- `references/bug-patterns-2026-06-17-round2.md` through `round6.md` — Detailed scan rounds
- `references/bug-patterns-2026-07-04-knowledge-distiller.md` — NP-69–NP-73 (Knowledge Distiller Round)
- `references/bug-patterns-2026-07-05-refactor-distiller.md` — NP-74–NP-78 (Refactor Distiller Round)

### Build & CI
- `references/build-pipeline-2026-06-17.md` — greybel-js incompatibilities
- `references/build-pipeline-2026-06-25.md` — PR #29 session details
- `references/build-session-2026-06-17.md` — Build pipeline + workarounds
- `references/p0-build-fixes-2026-06-19.md` — P0 build fixes
- `references/build-cleanup-2026-06-19.md` — Expanded P0 + CI fixes
- `references/repo-restructure-2026-06-27.md` — Repo restructure (80→25 broken files)
- `references/greyhack-build-status-review-2026-06-19.md` — Session build review
- `references/routerinfo-build-2026-06-18.md` — Import path fix details

### Community & Architecture
- `references/community-resources.md` — Steam guide, apt-get, salmon85, ftzi architecture
- `references/greybel-vs-interpreter-setup.md` — Interpreter with Mock-Env
- `references/greyscript-deployment.md` — Deployment details
- `references/yuno-tools-deployment.md` — In-game yuno-tools directory
- `references/awesome-hacking-greyhack-research.md` — Top-20 recommendations
- `references/hacking-session-2026-06-27.md` — Session insights, player profile, test results
- `references/greyhack-deployment-pitfalls-2026-06-22.md` — Deployment pitfalls

### Scripts (wiederverwendbare Werkzeuge)
- `scripts/greyhack-db-watchdog.py` — v2.0 (2026-07-06) — DB-Watchdog für Cron
- `scripts/greyhack-hitlist.py` — Phase-4-DB-Recon: unscanned LAN-IPs scannen, Bewerten, Report
- `scripts/pre-scan-np-patterns.py` — NPC-Pattern-Vorab-Scan für Bug-Audits
- `scripts/fix-single-line-if.py` — Auto-Fix für einzeilige `if X then Y end if`
- `scripts/scan-new-patterns.sh` — Shell-Script für neue Bug-Pattern-Scans

## 🧭 Related Skills (Cross-Cluster Navigation)

- **`skill-navigator`** (orchestration/) — Meta-Navigator for all 169 Hermes skills
- **`multi-agent-pitfalls-cheatsheet`** (orchestration/) — TRIGGER-WATCHLIST for `delegate_task` calls
- **`multi-agent-orchestration`** (orchestration/) — The 3-Expert Research PATTERN
- **`sqlite-forensic-diff`** (data-science/) — Generic SQLite DB diff methodology (row-count deltas, content diffs, password-pattern extraction, cross-DB joins via ATTACH). Load for any multi-DB forensic comparison.
