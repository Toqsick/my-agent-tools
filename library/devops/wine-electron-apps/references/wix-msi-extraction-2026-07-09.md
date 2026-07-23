# WiX/MSI Installer-Extraktion (Session 2026-07-09)

## Was das ist

WiX-basierte MSI-Installer (Reckhorn DSP-6 V3.3, viele andere Hersteller wie Microsoft, Adobe-Plugins, InstallShield-konvertierte Setups) bündeln den eigentlichen Inhalt als **MS-CAB-Datei in einem unbenannten Stream innerhalb des MSI-Compound-Files**. Die Dateinamen im CAB sind **GUID-basiert** (`_<32-hex>`) — die echten Dateinamen (z.B. `Default.dat`, `InitFile.dat`, `Reckhorn DSP-6.exe`) stehen in der MSI `File`/`Media` Tabelle, die wir oft nicht direkt parsen können.

## Schnell-Pattern: 7z MSI-Compound + CAB-Stream

```bash
# 1. ZIP entpacken (wenn nötig)
mkdir -p /tmp/staging && cd /tmp/staging
unzip -o /home/.../installer.zip

# 2. MSI mit 7z extrahieren (7z kann Compound-Files lesen)
mkdir -p msi-extract
7z x -y -omsi-extract/MSI "installer.msi"
# Ergibt alle Streams in msi-extract/MSI/

# 3. Das CAB ist der größte unbenannte Stream (~12 MB)
ls -laS msi-extract/MSI/ | head
#  → _6E2BA4DB2E4D35C067738B4A5999BB18  (12 MB = das CAB)

# 4. CAB in eigene Datei kopieren
mv msi-extract/MSI/_6E2BA4DB2E4D35C067738B4A5999BB18 file.cab

# 5. CAB entpacken (GUID-Filenamen)
7z x -y -oAPP file.cab
# Ergibt 87 Files mit GUID-Namen
```

## Echte Dateinamen identifizieren

Da die GUID-Filenamen nichts sagen, musst du per **Heuristik** oder **PDB-String-Match** identifizieren:

### PDB-String-Suche in PE-Files (für EXE/DLL)

```bash
# Strings aus großen EXE/DLL extrahieren — PDB-Pfad verrät Identität
strings APP/_<guid> 2>/dev/null | grep -E "\\\\.+\.pdb|AMPLIVE|MiniMax|Reckhorn" | head
# Output: \\AMPLIVE9_20120606\\AMPLIVE9_20131219\\Release\\SOUNDMAGUS DSP Utility.pdb
# → das ist die Hauptapp "SOUNDMAGUS DSP Utility" = Reckhorn DSP-6 Setup-Tool
```

### DLL-Klassen-Suche (für MFC/Win32)

```bash
# Strings der MFC-Klassen-Namen
strings APP/_<guid> 2>/dev/null | grep -E "^\\?AVC[A-Z][a-zA-Z]+@@" | sort -u | head
# Output: .?AVCMFCToolBarsCommandsPropertyPage@@
# → .?AV + C = MFC-Framework. Klassennamen wie CDspCtlThread, DSPUtilityApp, DSPUtilityDlg
# identifizieren die Hauptapplikation
```

### Größe + Typ-Heuristik

```bash
# Größte EXE = Hauptapp
ls -lS APP/_* | head
# → Reckhorn-DSP-6.exe (3.4 MB, MFC) + SOUNDMAGUS-DSP-Utility.exe (1.9 MB, native)
# Die kleinere, MIT PDB-String, ist die echte Hauptapplikation

# Treiber-DLLs: klein, native (PE32), heißen oft ...USB..., ...DRV...
strings APP/_<guid> 2>/dev/null | grep -E "usbxp|usblib|silab|ftdi|windrvr" | head
# → SiLib.sys + SiUSBXp.sys + SiUSBXp.dll (für SiLabs-Chips)
```

## Konfigurations-Dateien (DAT, PIC, INI)

Diese sind im CAB oft **getarnt als PNG** (kleine Icons mit Extension `.dat`/`.pic` in der File-Tabelle, aber tatsächlich binäre Daten). Identifizierung:

```bash
file APP/_<guid>  # zeigt "PNG image data" aber echter Use ist DAT
# Verdächtig wenn: kleine Datei, PNG-Magic-Header, aber kein visueller Sinn
# (z.B. 30 KB "PNG" mit 52x27 Pixel — das ist eine Resource, kein User-Asset)
```

Die App crasht oft leise wenn diese fehlen — daher: **bei App-Crash ohne Fehlermeldung: alle kleinen PNG-getarnten Files ins App-Verzeichnis kopieren.**

## MSI `File`-Tabelle parsen (für exakte Namen)

Wenn die Heuristik nicht reicht, ist die `File`-Tabelle im MSI die Wahrheit. Format ist proprietäres **IDFMT** (Microsoft Internal Database Format), benötigt `msitools` (libmsi) das in Ubuntu als `msitools` package verfügbar ist. Ohne `sudo apt install msitools` kann man auch:

```bash
# Direct aus dem _StringPool die Strings extrahieren
python3 <<'EOF'
with open("msi-extract/MSI/!_StringPool", "rb") as f:
    data = f.read()
# Strings sind UTF-16LE codiert
# String-Header: u16 refCount, u16 sizeLo, u16 sizeHi
# Aber Format ist komplex — meist einfacher, 7z + heuristik zu nutzen
EOF
```

Oder via `pip install msilib` (Windows-only) — funktioniert NICHT nativ.

## Wine-Registry für Config-Injection

Viele Apps speichern User-Config in der Windows-Registry (HKCU\Software\<App>\...).

```bash
WINEPREFIX=/path/to/bottle wine reg add 'HKCU\Software\MyApp\Settings' /v DarkMode /d 1 /f
# Verify
WINEPREFIX=/path/to/bottle wine reg query 'HKCU\Software\MyApp\Settings'
```

## Anwendungsfall-Beispiele

| App | Installer-Format | Größe nach Extraktion | Echte App-EXE |
|---|---|---|---|
| Reckhorn DSP-6 V3.3 | WiX MSI 12 MB | 818 MB (Bundle inkl. 8 MB TTF) | SOUNDMAGUS-DSP-Utility.exe (1.9 MB) |
| Generische MFC-App | WiX MSI 10-50 MB | 100-500 MB | meist größte EXE ohne DSP/Sound-Magical-Name |
| Adobe-Plugin | MSI (InstallShield konvertiert) | 50-200 MB | DLLs in Plugin-Verzeichnis |

## Lessons Learned

- **WiX/MSI Installer extrahieren ist mit 7z in 30 Sekunden erledigt** — kein `lessmsi`, `msiexec /a` oder Wine-Setup nötig
- **CAB-Stream ist immer unbenannt** im MSI (`_<random-hex>`) und **immer der größte Stream** — einfach `ls -lS msi-extract/MSI/` und der größte Eintrag
- **GUID-Filenamen sind nicht verloren**, sie sind absichtlich — die File-Tabelle mappt sie auf echte Namen, aber für die meisten Use-Cases reicht PDB-String + Klassen-Heuristik
- **Getarnte PNGs = Config-Files** sind ein beliebter MSI-Builder-Trick um File-Listen klein zu halten
- **Bei App-Crash ohne Fehlermeldung sind fehlende Config-DLLs** (`Reckhorn DSP-6DEU.dll`, `Reckhorn DSP-6LOC.dll`) eine sehr häufige Ursache
- **app.asar in Electron-Apps und .exe in MFC-Apps haben dieselbe MSI-Behandlung** — das Pattern ist nicht Electron-spezifisch
