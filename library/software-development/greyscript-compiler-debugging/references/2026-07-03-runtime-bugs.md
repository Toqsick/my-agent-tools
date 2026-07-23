# Yuno V6 Modular — Runtime Bug Analysis (2026-07-03)

## Context

5 GLM-5 workers dispatched for parallel deep-bug search on Yuno V6 modular code (10 modules, ~12KB each).
Workers checked 8 compiler-bug patterns. Found ZERO compiler bugs — all modules build clean.
But found 15+ RUNTIME bugs that would crash in-game.

## Bug Inventory by Module

### yuno_core.src (6.2KB → 6.3KB after fixes)
- ✅ 0 compiler bugs
- ⚠️ Worker false positives: 4 trailing-comma flags (legal in GreyScript)
- **Fixes applied:**
  - Added `"objectList":{}` to `YUNO_SHARED.main_session` init
  - Added `"netcatList":{}` to `YUNO_SHARED.main_session` init
  - Added `"vars":{}` to `YUNO_SHARED.main_session` init

### yuno_recon.src (3.7KB → 3.9KB)
- ✅ 0 compiler bugs
- **Runtime fix:** Added `commands = {targets: @cmd_targets, use: @cmd_use, back: @cmd_back, nmap: @cmd_nmap, exploitscan: @cmd_exploitscan, deepscan: @cmd_deepscan}` in dispatch footer

### yuno_attack.src (9.8KB → 9.9KB)
- ✅ 0 compiler bugs
- **Runtime fixes:**
  - Added `commands` dict (6 cmds) in dispatch footer
  - Added `obj = main_session.object` init
  - Fixed `read_configs(obj)` → `read_configs(pc)` (typo)
  - Removed duplicate `if not pc then return` block in cmd_loot
  - Removed duplicate `if not pc then return` block in cmd_defend

### yuno_files.src (8.1KB → 8.4KB)
- ✅ 0 compiler bugs
- **Runtime fixes:**
  - Added `commands` dict (11 cmds) in dispatch footer
  - Added `obj = main_session.object` init

### yuno_crypto_net.src (6.3KB → 6.5KB)
- ✅ 0 compiler bugs
- **Runtime fixes:**
  - Added `commands` dict (5 cmds) in dispatch footer
  - Added `obj = main_session.object` init

### yuno_macros.src, yuno_mission.src, yuno_snapshots.src, yuno_suggest_plugin.src, yuno_util.src
- ✅ 0 compiler bugs
- **Runtime fixes:** Added `commands` dict per module (6/4/3/3/13 cmds)
- yuno_util, yuno_macros: also added `obj = main_session.object` init

## Key Findings

1. **Static scan (parent) and subagent review (workers) are ORTHOGONAL** — they find different bug classes
2. **ALL 10 modules compiled clean** — the modular split generated syntactically correct code
3. **ALL 10 modules had the SAME runtime bug** — missing `commands` dict in dispatch footer
4. **50% of modules had missing `obj` init** — yuno_files, yuno_attack, yuno_crypto_net, yuno_util, yuno_macros
5. **1 typo bug** — `read_configs(obj)` vs `read_configs(pc)` in yuno_attack
6. **2 dead-code blocks** — duplicate `if not pc then` guards in yuno_attack
7. **Worker false positives:** trailing commas flagged 4× (legal in GreyScript)

## Template for Future Runs

When spawning subagents for code review:
```python
delegate_task(tasks=[{
    "goal": f"Deep Bug Search auf {filename}",
    "context": f"""
    Prüfe {filename} ({size}B, {lines} Zeilen) gegen diese Compiler-Bug-Patterns:
    1. String-in-String ("text \"inner\" text")
    2. Komma-Bugs (fehlendes Komma zwischen Object-Einträgen!)
    3. //-Kommentare in Object-Literalen
    4. Doppelte //command: Marker
    5. """" vier+ aufeinanderfolgende Quotes
    6. Fehlende end function / end if (Balance)
    7. Zugewiesener Code statt Function ('cmd_X.run = ...' ohne 'cmd_X = {}')
    8. Body ohne Function Header (Code nach 'end function' ohne function()

    ACHTUNG: GreyScript 0.9.6771-beta erfordert TRAILING COMMAS (letzter Eintrag in {} hat Komma).
    Fehlende Kommas sind BUGS, zusätzliche Kommas sind LEGAL.

    KEINE Änderungen, KEINE Patches — nur Read-Only Analyse.
    
    Für RUNTIME Bugs achte auf:
    - Ist 'commands' Dict definiert bevor commands.hasIndex() aufgerufen wird?
    - Ist 'obj = main_session.object' gesetzt?
    - Sind alle main_session Felder initialisiert (objectList, netcatList, vars, targets, sessions)?
    - Gibt es Variable-Typos (z.B. 'obj' statt 'pc')?
    - Gibt es doppelte if-not-X-then-return Blöcke (dead code)?
    - Wird 'try_exploit', 'read_configs', 'COMMON_PORTS' etc. definiert bevor es referenziert wird?
    
    Berichte als JSON mit: file, bugs_found[line, type, description, current, fix], summary[total_bugs, by_type]
    """
}])
```

## Lessons Learned

1. **Always run BOTH static scan AND subagent review** — they find different things
2. **Workers need explicit note about trailing commas** — they commonly flag these as bugs when they're legal
3. **Parent should fix bugs while workers run** — Phase 2 pattern from multi-agent-orchestration
4. **Cross-check worker findings before applying** — workers have blind spots too
5. **`commands` dict is ALWAYS the #1 runtime bug** in modular GreyScript code
