# Live-Log-Reading nach Game-Start

Nach dem Game-Start via `tail -f` die RED4ext-Logs im Game-Root lesen:

```bash
tail -f "$CP77_ROOT/red4ext.log"
```

**Erwartete Signale (Good Sign):**
```
[RED4ext] Initializing...
[RED4ext] Plugin ArchiveXL loaded
[RED4ext] Plugin TweakXL loaded
[RED4ext] Plugin Codeware loaded
[RED4ext] Initialization complete
```

**Warnsignale:**
```
[RED4ext] ERROR: Failed to load Plugin Foo
[RED4ext] WARN: Incompatible version
[RED4ext] FATAL: ...
```

**CET-Log** (falls vorhanden): `$CP77_ROOT/cyber_engine_tweaks.log`