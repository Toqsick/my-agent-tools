# azahar-facts.md — Build, CLI und Automatisierungsfakten (Stand Sep. 2026, master)

Quellen: azahar-emu/azahar (Repo/Wiki/master-Quelltext), pokerogue-3ds-Praxis.

## Identität

- Community-Fortführung von Citra (Merge aus PabloMK7-Fork + Lime3DS), C++/Qt6,
  GPL-2.0+; CMake-Projektname ist intern noch `citra`
- Frontends: `citra_qt` (der Emulator, GUI), `citra_cli` (**nur** ROM-Kompression,
  kein Emulator!), `citra_room(_standalone)` (Multiplayer-Rooms), `citra_libretro`
  (Core, `ENABLE_LIBRETRO=OFF` default), `tests` (Catch2)

## Linux-Build

```bash
# Abhängigkeiten (Ubuntu 24.04): cmake qt6-base-dev qt6-multimedia-dev libSDL2-dev
# qt6-tools-dev … (Wiki: Building-From-Source; CMake ≥ 3.22, GCC 11+/Clang 18, Qt ≥ 6.2)
cmake -B build -S . && cmake --build build -j"$(nproc)"
# Docker-Schnellweg (CI-Image des Projekts):
docker run --rm -v "$PWD":/src opensauce04/azahar-build-environment:latest
```

CI des Upstream (`build.yml`) baut AppImage/Windows/macOS/Android + libretro-Core;
`format.yml` ist ein clang-format-Gate (lokal formatieren, bevor man PRs gegen
den Fork stellt).

## Qt-Frontend-CLI = die Automatisierungsfläche

`src/citra_qt/main.cpp` (GMainWindow-Arg-Parsing):

| Arg | Wirkung |
|---|---|
| `<rom>` (Positional) | ROM booten (`BootGame` direkt) |
| `-p/--movie-play <file>` | TAS-Movie abspielen (deterministische Eingabewiederholung) |
| `-r/--movie-record <file>` / `-a author` | Movie aufzeichnen |
| `-d/--dump-video <path>` | Video-Dump des Laufs |
| `-g/--gdbport <port>` | GDB-Stub (skriptbares Introspezieren von Speicher/Registern) |
| `-i/--install <cia>` | CIA installieren |
| `-f` / `-w` | Fullscreen / Windowed |

Headless-Wege: **kein natives Headless-Frontend, kein Lua** (Citras Lua-Engine wurde
gestrichen; Panda3DS wäre die Lua-Alternative). Praktikabel:
1. Qt-Frontend unter Xvfb/`-platform offscreen` mit ROM-Arg (das pokerogue-Muster)
2. libretro-Core unter headless libretro-Harness (CI-tauglichste Option)
3. `ENABLE_TESTS=ON` + `ctest` für Unit-Ebene
4. `-g` GDB-Stub für skriptgesteuerte Speicherinspektion

## Betriebs-Gotchas aus der Praxis (pokerogue tools/emu)

- **SIGTERM wird verschluckt**: Prozess nicht einzeln killen — Prozessgruppe
  abbauen/Xvfb-Display beenden
- **`pgrep -f azahar` wertlos**: matcht die eigene Kommandozeile → PID der geforkten
  Kind-Prozesse sauber registrieren (proc.py-Muster)
- **RPC antwortet vor `main()`**: frühe Antworten sind Framework-Ready, nicht
  Spiel-Ready; `wave_==0` ist ein Null-Muster
- **NVIDIA-modeset-Hang** (manche Hosts, seit 09.09. beobachtet): GL-Init hängt →
  LD_PRELOAD-Shim + Mesa-Software-GL (Workaround-Doku in pokerogue
  docs/evidence-README); Emulator-Ausfall ist nie Task-Blocker — Timebox,
  Checkliste an Menschen, weiter
- **Sysfont aus eigenem NAND**: Azahar liefert den Shared-Font aus dem eigenen
  Konsolen-NAND-Dump — nicht beschaffbar für CI, Grund für lokal-statt-CI

## Beweis-Hierarchie (was zählt)

1. Neuer Save-File mit gültiger CRC (bestes Signal — das Spiel selbst hat geschrieben)
2. RPC-gelesener Zustand aus dem unmodifizierten Release-Binary (Kein-Hook-Regel)
3. Boot-Klassifikation (ok/warm/error-screen/timeout)
4. Video-Dump/Screenshots (nur Illustration, nie Beweis)

## Verwandte Fakten

- Artefakte des Upstream sind Nintendo-sauber; eigener CI-Smoke-Test nutzt frei
  verteilbare Homebrew-3DSX (z. B. Universal-DB) statt Spiele-ROMs
- `citra_room` separat buildbar, wenn Netplay-Rauchtests gebraucht werden
- Fork-Strategie für eigene Harness-Änderungen am Emulator: vermeiden — der Orakel-
  Ansatz (Save/RPC/GDB) misst am ausgelieferten Artefakt, ohne den Emulator anzufassen
