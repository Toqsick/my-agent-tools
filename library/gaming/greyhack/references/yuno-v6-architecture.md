# YUNO V6 Architecture Reference

**Status:** Build OK (greybel ✅ 0 Errors) · **Date:** 2026-07-03  
**Size:** 78.2 KB Source / 46 KB Build / 61 Commands  
**Base:** V5 (~65 KB, 50 Commands, 2107 Zeilen)

---

## V6 Overview — 6 Neue Features

| # | Feature | Datei | Code-Delta | Beschreibung |
|---|---------|-------|------------|-------------|
| 1 | **Disk-Persistenz** | `yuno_v6.conf` + `save_config()` + `load_config()` | ~3 KB | Config-File write/read beim exit/start |
| 2 | **Full State Restore** | `save_snapshot()` + `restore()` | ~1 KB | Vars, Missions, Plugins, Theme zurücksetzen |
| 3 | **Plugin Auto-Load** | `macros` + `load_config()` scan | ~1 KB | Macros-Ordner scannen beim Start |
| 4 | **History-aware Suggest** | `smart_suggest()` V6-Upgrade | ~1 KB | Frequenz-basierte Command-Empfehlung |
| 5 | **Sniffer Integration** | `smart_suggest()` V6-Upgrade | ~0.5 KB | Metaxploit-Sniffer Kontext |
| 6 | **Cooperative Mode** | `cmd_coop*()` + `coop_manager` Map | ~3 KB | Multi-User Framework |

## Config-PIPE Schema

**Datei:** `/home/gregor/Config/yuno_v6.conf` (autogeneriert beim ersten `exit`)

```
# PIPE-delimited Format — Prefix + Values
# Zeilen ohne Pipe werden als Kommentar ignoriert

M|mission1|Hack Reraldi|Access daemon port 8765|0    # M = Mission
V|my_ip|142.32.54.56                                    # V = Variable
P|/home/gregor/Config/my_tool.src|my_tool|1234         # P = Plugin
S|before_mission|default|3|2|5|YUNO_V5_snap            # S = Snapshot
H|nmap|199.229.146.172                                  # H = History
```

### Feldbedeutung pro Prefix

**M (Mission):** `ID | Name | Beschreibung | DoneFlag`
- DoneFlag: `0` = offen, `1` = erledigt

**V (Variable):** `Key | Value`

**P (Plugin):** `Path | Name | Size`

**S (Snapshot):** `Name | Theme | TargetCount | MissionCount | PluginCount | SourceVersion`

**H (History):** `Command | Arg`
- Max 30 Einträge (älteste werden beim Laden verworfen)

### Laden (beim Start)

```greyscript
load_config:
  1. pc.File(yuno_v6.conf) → get_content → split(char(10))
  2. Jede Zeile: split("|") → prefix-basierte Map-Zuordnung
  3. Missions → missionList[], Vars → mapVars[], Plugins → mapPlugins[]
  4. Snapshots → snapshotList[], History → mapHistory[]
  5. Kein File → silent-pass (erster Start → Config wird beim ersten exit erstellt)
```

### Speichern (beim Exit + manuell via `save-yuno`)

```greyscript
save_config:
  1. Build lines = []
  2. Für jedes Element in jeder Liste: join mit "|" + Prefix
  3. pc.touch(yuno_v6.conf) → set_content(lines.join(char(10)))
  4. Nur bei Änderungen → sonst skip
```

## Fork-and-Extend Workflow

**Pattern:** V5 → V6 (large framework extension, keine Neuschreibung)

```
1. Read V5 vollständig
   - Verstehe dispatcher, state-objects, command-registry, load-chain
   - 2107 Zeilen in 3 Chunks (700 Zeilen / read_file)

2. Plan Features
   - Jedes Feature = ein Patch zwischen bestehende Blöcke
   - Keine signaturänderungen an bestehenden Funktionen!

3. Patchen (6 Patches)
   - Feature 1: save_config/load_config nach der Main-Loop
   - Feature 2: snapshot/restore als neue Subroutinen
   - Feature 3: macros scan in load_config integriert
   - Feature 4: smart_suggest() upgrade mit history+sniffer
   - Feature 5: sniffer-check in suggest eingebaut
   - Feature 6: cmd_coop_* als neue Befehle im Dispatcher

4. Build-Verifikation
   npx greybel build yuno_v6.src -u

5. Mock-Env Smoke-Test
   npx greybel execute /build/yuno_v6.src -p help --silent

6. Kopieren nach ~/greyhack-tools/
   cp /build/yuno_v6.src ~/greyhack-tools/yuno_v6.src
```

**Lessons Learned:**
- Config-Speicher = Game-Changer für Daily-Driver — kein Missions-Verlust mehr nach Exit
- PIPE-delimited Format ist einfacher als JSON für GreyScript (kein parse_json, kein key traversal)
- Auto-Save on Exit verhindert vergessenes Speichern
- State-Restore nur für serialisierbare Daten (Shell-Objekte = neu aufbauen)
- Coop-V6 = Framework-only (echtes Netcat in V6.1+)
- Mock-Env hat KEINEN persistenten Speicher — Persistenz nur im Spiel testbar

## In-Game Deployment

```
CodeEditor → New → Paste yuno_v6.src → Save → Build → Run
```

Alternativ: SQLite-DB-Edit (siehe `references/in-game-db-edit.md`).

Config wird auto-erstellt: `/home/gregor/Config/yuno_v6.conf`

---

See also:
- `~/docs/system/greyhack-yuno-v6-2026-07-03.md` — Full session doc + smoke test checklist
- `~/greyhack-tools/yuno_v6.src` — Build file (46 KB, in-game ready)
- `~/greyhack-tools/yuno_v6_source.src` — Source file (78 KB, with comments)
