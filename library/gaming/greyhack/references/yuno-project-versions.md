# YUNO Project — Versionen & Features

## Projektübersicht

Das YUNO-Projekt ist die Basti-spezifische Ausprägung des All-in-One Scripter-Patterns. Fünf Versionen:

| Version | Größe | Features | Verfügbar als |
|---------|-------|----------|---------------|
| **V1** | 17 KB | 7 Subcommands, early-exit dispatcher | `templates/yuno-all-in-one.src` |
| **V2** | 45 KB | 50+ Commands, interactive `user_input()`-Shell, `main_session`-State, auto-lib-load, auto-hack/loot/defend/bank | `~/docs/system/greyhack-yuno-v2-2026-07-03.md` |
| **V3** | 52 KB | V2 + Theme-System (3 themes via Map-Switch) + Macro-System (`@<name>`) + getyuno | `~/docs/system/greyhack-yuno-v3-2026-07-03.md` |
| **V5** | ~66 KB | V3 + Bugfixes + P0-Fixes + Syntax + CI-grün (19/19). ✅ **Confirmed running in-game 2026-07-03** — 50+ Commands, `//command:` Marker + CodeEditor gefixt. Alle 3 Libs geladen (cryptoLib, aptclient, MetaxploitLib). | `~/greyhack-tools/yuno_v5_source.src` |
| **V6** | 78.2 KB Source → 45.7 KB Build | V5 + 6 neue Features: Disk-Persistenz, Full State Restore, Plugin Auto-Load, History-aware Suggest, Sniffer-Integration, Cooperative Mode. **⚠️ Source (78KB) nicht mehr auf Disk — nur Build (45KB) in `/home/bratan/greyhack-tools/build/yuno_v6.src`**. Build ist uglified (169 minifizierte Funktionen), kein modularer Split möglich. | Build + `/home/bratan/build/yuno_v6.src` |
| **V6c** | 18 KB / 599 Z. | **Clean Minimal Edition** — lesbares, modulares GreyScript (keine Viper-Kompression). State-Persistenz + Top-10-Commands. Ideal als Startvorlage. | `templates/yuno-v6c.src` |

## Deltas

**V3-V5-Delta:** Von 52 KB auf ~65 KB durch 51 Syntax-Fixes, P0-Bugfixes, CI-Stabilisierung (19/19 Builds grün).

**V5-V6-Delta:** Von ~66 KB Build auf 45.7 KB Build (uglified, 169 minifizierte Funktionen). +6 Feature-Gruppen (Disk-Persistenz, State Restore, Plugin Auto-Load, History Suggest, Sniffer, Coop). **⚠️ V6 Build ist monolithisch (45 KB) — uglified, kein modularer Split. Source (78 KB) nicht mehr auf Disk.** Build via DB-Injection in Config/ deploybar.

**Vergleich zu Viper (EntitySeaker):** Viper = 162 KB / 94 files / 85 commands. YUNO V6 modular = 10 Module à ~6-11KB / 61 Commands — **52% kleiner mit gleicher Kern-Funktionalität + YUNO-Killer-Features.**

## Wann welche Version

- **V1 (17 KB)** für simple Tools (scan/hack/loot) ohne interactive shell
- **V2 (45 KB)** für 30+ Commands mit State-Management (auto-hack, sessions, crypto)
- **V3 (52 KB)** für Full-Feature-Frameworks (Theme, Macros, multi-instance)
- **V5 (~66 KB)** für stabilen Daily-Driver (P0-sauber, 50+ Commands, CI-grün, ✅ **in-game getestet**)
- **V6 (modular, 10× <12KB)** für **Disk-Persistenz** (Config speichern/restoren) + Cooperative Mode — erfordert modularen Build
- **V6c (18 KB / 599 Z.)** für **lesbare, minimalistische Tools** — State + Top-10-Commands. Ideal als **Startvorlage**: Keine Viper-Kompression, sauber an Funktionsgrenzen, modular erweiterbar. **Wann:** Learning-Phase, eigene Tools bauen, schnelle Prototypen, oder wenn die Viper-Codebase zu unübersichtlich ist.

## Fork-and-Extend Workflow (V5→V6)

1. V5-Code vollständig lesen (2107 Zeilen in Chunks) — Struktur verstehen
2. Features als Patches zwischen bestehende Code-Blöcke einfügen (keine Neuschreibung)
3. Mit `npx greybel build yuno_v6.src -u` verifizieren
4. Mit `npx greybel execute /build/yuno_v6.src -p help --silent` Mock-Env testen
5. Nach Build: Build-File (45 KB) in `~/greyhack-tools/build/` deployen. **⚠️ V6 Source (78 KB) nicht mehr vorhanden — nur der uglified Build. Für Source-Edits: V5 Source oder V6c Template nutzen.**

## Build-Befehl

```bash
npx greybel build yuno_v6.src -u
# → /home/bratan/build/yuno_v6.src (Build, 46 KB)
```

## In-Game Install

`~/docs/system/greyhack-yuno-v6-2026-07-03.md`, `references/in-game-db-edit.md` Workflow.