# Windows Desktop Apps auf Linux — Non-Electron (WinForms, .NET, Win32)

> Ergänzung zu `references/windows-apps-on-linux.md` (Electron-Fokus).
> Diese Datei: klassische Win32/WinForms/.NET-Apps ohne Electron-Chromium-Renderer.

## Anwendungsfall

App ist **nicht** Electron — erkennbar an:
- Kein `app.asar` im Bundle
- Kein `@hilodesktop-updater`-Marker
- PDB-Path verweist nicht auf Electron (z.B. `\AMPLIVE9_20131219\Release\SOUNDMAGUS DSP Utility.pdb` = native C++/MFC/WinForms, nicht `app.asar.unpacked\node_modules\...`)
- Strings zeigen auf `MFC`, `WinForms`, `RegisterApplicationRestart`, `SiUSBXp.dll` (native DLLs), `KERNEL32.GetProcessInformation`
- MSI-Installer (WiX 3.x) statt NSIS

## MSI-Installer-Extraction (ohne msitools)

**`msiextract` braucht `msitools`-Paket** (oft nicht installiert). Eleganter: **7z kann MSI-Compound-Files direkt lesen**, und das Payload-CAB ist als hidden GUID-Stream eingebettet.

```bash
# 1. MSI entpacken (7z versteht Compound Document File V2)
mkdir -p msi-extract
7z x -y -omsi-extract/MSI setup.msi

# 2. Inhalt prüfen — du siehst MSI-Tabellen (File/, Media/, Component/) + ein großes Stream
ls -la msi-extract/MSI/   # → _6E2BA4DB2E4D35C067738B4A5999BB18 = 12MB CAB

# 3. CAB (das ist der hidden Stream mit den App-Files) extrahieren
mv msi-extract/MSI/_6E2BA4DB2E4D35C067738B4A5999BB18 setup.cab
7z x -y -osetup-cab setup.cab
# → 87 Dateien mit GUID-Filenamen (z.B. _F41861EAE630493CA14D1698C1A905C6 = App.exe)
#   Plus Default.dat/InitFile.dat/Res.Pic etc. — Extensions sind getarnt
```

**GUID-Filenamen auflösen** (MSI `File`/`Media` Tabelle parsen):
- `lessmsi` falls vorhanden: `lessmsi l setup.msi` listet mit echten Dateinamen
- Sonst Python mit `python-msi` / `msilib` (builtin) für Tabelle-Parse
- Strings-Suche nach Marker-Strings: die EXE mit "Reckhorn" / "DSP Utility" / bekannten PDB-Pfaden ist die Hauptapp

**Pragmatisch (oft ausreichend):**
```bash
# Datei-Typen erkennen
for f in setup-cab/_*; do
  type=$(file -b "$f" | head -c 50)
  if [[ "$type" == *"PE32 executable"* ]]; then
    echo "$f: $type"
  fi
done

# Strings-Suche nach App-Namen
for f in setup-cab/_*; do
  if strings "$f" 2>/dev/null | grep -qE "AppName|ProductName"; then
    echo "FOUND: $f"
  fi
done
```

**Wichtige Defaults in WiX/MSI-Bundles:**
| Datei (GUID-Name) | Echter Name | Inhalt |
|---|---|---|
| `_F41861EA...` | `Reckhorn DSP-6.exe` | Hauptanwendung (1,9 MB) |
| `_D97CFB8D...` | (zweite EXE) | Helper/Plugin (3,4 MB) |
| `_F8CCC9E12...` | `SiUSBXp.dll` | Native USB-Wrapper (90 KB) |
| `_67FBB0E2...` | `SiLib.sys` | USB-Treiber (14 KB) |
| `_990D182C...` | `SiUSBXp.sys` | USB-Treiber moderner (17 KB) |
| `_37BDD404E...` | (Font) | TrueType/OpenType (8,8 MB) |
| `_F41D944E...` | (Icon) | PNG getarnt (36 KB) |

## Wine-Prefix ohne Bottles-Manager (schneller Alternative-Pfad)

Wenn Bottles-Manager zu langsam oder zu restriktiv ist, kann ein Wine-Prefix direkt
angelegt und mit App-Files befüllt werden — Bottles erkennt ihn dann als "custom" Bottle.

```bash
APP_PREFIX="$HOME/.var/app/com.usebottles.bottles/data/bottles/bottles/AppName"
WINE_BIN="$HOME/.var/app/com.usebottles.bottles/data/bottles/runners/kron4ek-wine-11.11-amd64/bin/wine"

mkdir -p "$APP_PREFIX"
export WINEPREFIX="$APP_PREFIX"
export WINEESYNC=1 WINEFSYNC=1 WINEDEBUG=-all
export PATH="$(dirname $WINE_BIN):$PATH"

# 1. Prefix initialisieren (legt drive_c/, system.reg, .NET 4.7 an)
"$WINE_BIN" wineboot --init      # ~1.6 MB, 5-10s

# 2. App-Files reinkopieren
DEST="$APP_PREFIX/drive_c/Program Files/AppName"
mkdir -p "$DEST"
cp -v setup-cab/AppName.exe "$DEST/"
cp -v setup-cab/native.dll "$DEST/"

# 3. Native DLLs/SYS auch in system32 (für globale Sichtbarkeit)
cp -v setup-cab/native.dll "$APP_PREFIX/drive_c/windows/system32/"

# 4. Bottles-Manager-kompatibles Marker-File
cat > "$APP_PREFIX/bottle.yml" <<EOF
name: AppName
runner: kron4ek-wine-11.11-amd64
arch: win64
state: 0
created: $(date +%Y-%m-%d)
path: AppName
custom: true
EOF

# 5. Starten
"$WINE_BIN" "$APP_PREFIX/drive_c/Program Files/AppName/AppName.exe"
```

**Vorteil:** Sekunden statt Minuten Bottles-GUI, volle Kontrolle über Files, Bottles erkennt es.
**Nachteil:** Keine Bottles-Metadaten (Versionierung, Backup-Profile, Runtime-UI).

## WinForms + .NET Render-Diagnose

Anders als Electron-Apps (Heartbeat + Child-Process-Health) zeigen WinForms-Apps
einen anderen "lebt-aber-malen-nicht"-Indikator. Schlüssel-Signale in WINEDEBUG=+all
Log:

```
002c:err:wineboot:process_run_key Error running cmd L"C:\\windows\\system32\\winemenubuilder.exe -a -r" (2)
  → Bekannter Wine-Bug, ignorierbar

0024:fixme:heap:RtlSetHeapInformation HEAP_INFORMATION_CLASS 1 not implemented!
  → .NET-Init: Wine fehlt Heap-Optimization, NICHT fatal

0024:fixme:nls:RtlGetThreadPreferredUILanguages ...
0024:fixme:nls:get_dummy_preferred_ui_language ... returning a dummy value
  → Locale-Lookup, normal

0024:fixme:process:RegisterApplicationRestart (L" /RestartByRestartManager:...", 0)
  → ⭐ SMOKING GUN: .NET/WinForms Application.Run() hat begonnen
  → Wenn danach Stille, crashed die App nach Window-Create

0024:fixme:shell:InitNetworkAddressControl stub
  → Win32-Standard-Init, normal
```

**Wenn `RegisterApplicationRestart` der letzte Eintrag ist** → App hat das
`Form`-Objekt erzeugt, ist aber vor dem ersten `Show()`/`Paint()` gecrasht. Häufige
Ursachen: fehlende Config-Files, .NET-Version-Mismatch, fehlende native DLL.

**Prozess-Diagnose (analog Electron-Pattern):**
```bash
pgrep -af "AppName.exe|wineserver" | grep -v pgrep
# → bei laufender App siehst du AppName.exe + wineserver
# → wenn nur wineserver läuft, ist App.exe gecrasht

DISPLAY=:1 xwininfo -root -children | grep -iE "appname"
# → 1x1+0+391 = Wine-Chromium-Pseudo-Windows ODER Win32 unsichtbare Helper-Fenster
# → "Default IME" als Klassenname = Pre-Show-Phase (App hat Form erzeugt, aber nicht gemalt)
# → Korrekte Main-Window: 800x600+ mit korrektem Klassennamen
```

**Heartbeat-Surrogate für WinForms:**

WinForms-Apps senden keinen Heartbeat. Stattdessen:
- **Window-Count stabilisieren:** Wenn die App 4-5 Helper-Windows erzeugt und
  dann für >30s stabil bleibt, lebt sie. Prozess-Count + Window-Count zusammen sind
  gute Stabilitäts-Indikatoren.
- **Disk-Writes:** `~/.wine/drive_c/users/$USER/AppData/Roaming/AppName/` —
  wenn Files darin geupdatet werden (config.xml, settings.dat), arbeitet die App.
- **USB-Device-IO:** Bei DSP/Hardware-Tools: `lsusb` zeigt ob das Gerät
  angesprochen wird, oder `usbhid-dump`/`usbmon` für detaillierte USB-Traffic.

## Bekannte Pitfalls (WinForms + .NET + Wine)

| Symptom | Ursache | Fix |
|---|---|---|
| Main-Window = 1x1+0+391 | App hat Form erzeugt, vor `Show()` gecrasht | Config-Files (Default.dat etc.) fehlen → aus CAB extrahieren |
| Heartbeat kommt, aber UI rendert nicht | DirectX 9 fehlt im X-Server | `winetricks d3dx9 d3dcompiler_43` oder DX9-Override |
| Crash bei `.NET 4.7`-Init | Mono-Compat-Layer für ältere App | `winetricks dotnet35` zusätzlich |
| App braucht USB-Hardware | DSP/Controller-Tools prüfen Geräte-Existenz | Ohne echtes Gerät: oft Splash + Crash ohne Message |
| Aero-Glass-Effekte fehlen | X-Server ohne Compositing | `winetricks d3d9` oder `--disable-gpu` im App-Start |
| `RegisterApplicationRestart` → Stille | .NET-WinForms-Init-Crash | Config-Files prüfen, Mono statt Wine-fallback-Mono |

## Lessons Learned 2026-07-09 (Reckhorn DSP-6 mini)

1. **MSI-Payload via 7z extrahierbar** ohne `msitools` zu installieren. Das CAB
   ist als unbenannter Stream im Compound-File versteckt, aber 7z findet es.
2. **GUID-Filenamen in WiX-Bundles** sind Tarnung — die echten Namen werden zur
   Laufzeit aus der `File`/`Media`-Tabelle aufgelöst. Pragmatische Heuristik:
   Datei-Typ + Strings-Suche nach App-Markern.
3. **Wine-Prefix direkt (ohne Bottles-Manager)** ist 10x schneller. Bottles-CLI
   ist zu restriktiv (nur via Flatpak-Sandbox).
4. **WinForms-Apps crashen "leise"** ohne USB-Hardware. Heartbeat-Ersatz:
   Process-Count + Window-Count + Disk-Writes.
5. **`RegisterApplicationRestart` ist der .NET-Lebensbeweis.** Wenn danach Stille
   → App hat `Form`-Objekt erzeugt, ist vor `Show()` gecrasht.
6. **`wineboot --init`** legt automatisch .NET 4.7.03190 + Wine-Mono 2.0 an.
   Kein manuelles `winetricks dotnet48` nötig für moderne WinForms-Apps.

## Verwandte Doku

- `references/windows-apps-on-linux.md` — Electron-Fokus (NSIS, OAuth, Custom-Protocol)
- `~/docs/system/reckhorn-dsp-6-bottles-2026-07-09.md` — Reckhorn Setup-Doku
- `~/docs/system/minimax-hub-bottles-2026-07-03-FINAL.md` — MiniMax Hub Setup (Electron-Schwester)
