# Galaxy-Health-Bridge 2026-07-19 — Validation Case

> Concrete worked example for the self-verify gates pattern. 3 subagents,
> 3 different output types, all used numerical verification gates.
> 0 Queen patches needed post-first-pass.

## Briefing-Verification-Gates (Original aus der Session)

### Biene 1 (Doku — ~/docs/system/galaxy-watch6-selfhost-setup-2026-07-19.md)

```text
VERIFY (PFLICHT — beide Checks):
  1. `wc -l ~/docs/system/galaxy-watch6-selfhost-setup-2026-07-19.md`
     — Minimal 40 Zeilen.
  2. `wc -w ~/docs/system/galaxy-watch6-selfhost-setup-2026-07-19.md`
     — Sollte zwischen 1200 und 1800 liegen.
  Bei <= 1200: Prosa verdichten, fehlende Sektionen ergänzen.
  Bei >= 1800: Straffen, Redundanzen entfernen.
```

### Biene 2 (Kotlin-Skeleton — ~/10-Projekte/.../health-bridge/)

```text
VERIFY (PFLICHT — zwei separate Checks):
  1. `find ~/10-Projekte/10-active/projects/health-bridge/ -type f | wc -l`
     — Sollte >= 15 sein
  2. `find ~/10-Projekte/10-active/projects/health-bridge/ -name "*.kt" | wc -l`
     — Sollte >= 8 sein
```

### Biene 3 (InfluxDB-Schema + Grafana — .../health-bridge/influxdb-schema/ + grafana/)

```text
VERIFY (PFLICHT — alle drei, in Reihe):
  1. `python3 -c "import json; json.load(open('.../dashboard.json'))"` — JSON-Check
  2. `ls -la ~/10-Projekte/.../grafana/dashboard.json` — Datei-Existenz
  3. `find ~/10-Projekte/.../influxdb-schema -type f | wc -l` — >= 3 Schema-Dateien
```

## Result

| Biene | Verzeichnis | Output | Gates | Verified |
|-------|-------------|--------|-------|----------|
| Atta (Doku) | `~/docs/system/` | galaxy-watch6-selfhost-setup-2026-07-19.md | wc -l, wc -w | ✅ |
| Bombus (Kotlin) | `~/10-Projekte/.../health-bridge/` | 15+ files, 8+ .kt | file count, .kt count | ✅ |
| Caelifera (Schema) | `.../health-bridge/{influxdb-schema,grafana}/` | 4 files | JSON parse, file count | ✅ |
