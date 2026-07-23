# vapor — Linux-native CLI CP77 Mod-Manager

**Source:** [Elsie19/vapor](https://github.com/Elsie19/vapor) (12 Stars, Rust, GPLv3)
**Stand:** Juli 2026 — kein Binary, nur Source. Letzter Commit 2026-04-25.

## Überblick

vapor ist ein CLI-Tool (Rust) zum Verwalten von CP77-Mods auf Linux. Tracked welche Dateien zu welchem Mod gehören, ermöglicht Enable/Disable und zeigt einen Graph der Mod-Abhängigkeiten. **Low-Level:** keine automatische Dependency-Auflösung, kein Version-Check, kein Cloudflare-Umgehung.

## Bauen

```bash
# Voraussetzung: Rust
rustc --version  # check
# Falls nicht vorhanden:
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# Klonen
git clone https://github.com/Elsie19/vapor ~/cp77-modding/tools/vapor
cd ~/cp77-modding/tools/vapor

# Bauen (Release, ~5 Min)
cargo build --release

# Binary:
ls -lh ~/cp77-modding/tools/vapor/target/release/vapor
# ~7-10 MB
```

## Verwendung

```bash
# Initialisierung (einmalig)
vapor init
# → Fragt nach CP77 Game-Root: /path/to/Cyberpunk 2077

# Mod hinzufügen
vapor add ~/cp77-modding/downloads/12345-ModName.zip --name "Mod Name" --version "1.0" --dependencies "ArchiveXL,Codeware"

# Status
vapor status        # Text-Ausgabe
vapor status --json # JSON für Weiterverarbeitung

# Enable/Disable
vapor disable "Mod Name"
vapor enable "Mod Name"

# File-Liste
vapor list "Mod Name"           # Welche Dateien zu einem Mod gehören
vapor list                      # Alle installierten Mods

# Dependency-Graph
vapor graph
```

## Pro-Tipp: Bulk-Install

```bash
for zip in ~/cp77-modding/downloads/*.zip; do
    name=$(basename "$zip" | sed 's/^[0-9]*-//;s/\.[^.]*$//')
    vapor add "$zip" --name "$name"
done
```

## Grenzen / Bekannte Issues

- **Kein Binary** (Stand Juli 2026) → muss aus Source gebaut werden (Rust + Cargo)
- **Keine Cloudflare-Umgehung** → Downloads müssen separat via Browser erfolgen
- **Nur CP77** → single-game focused, kein generischer Mod-Manager
- **Kein Update-Check** → keine Benachrichtigung wenn Nexus neue Version hat
- **Kein Load-Order Management** → vertraut auf RED4ext/CET für Reihenfolge
- **Patch-2.21-Kompatibilität** ungetestet (Repo zuletzt April 2026)

## Alternativen

| Tool | Sprache | Stars | Binary | Status |
|---|---|---|---|---|
| **vapor** (Elsie19) | Rust | 12 | ❌ Source-only | aktiv |
| **CyberpunkModManager** (Klemmbaustein) | C++/Qt | 4 | ❌ Build nötig | WIP, Win-focus |
| **linux-cyberpunk2077-mod-organizer** (AurelioAguirre) | Python | 0 | ❌ | veraltet |
| **simple-cyberpunk-mod-manager-for-linux** (pointdotpoint) | TS | 0 | ❌ | veraltet |

## Fazit

vapor ist brauchbar für **kleine Mod-Sets (<30 Mods)** ohne komplexe Dependencies. Für große Collections (City of Dreams Lite mit 444 Mods) ist es zu Low-Level. Der beste Workflow bleibt: **Browser-Download (manuell) → Sortier-Skript → Smoke-Check**.
