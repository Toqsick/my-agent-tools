# Native Win32 / MFC Apps unter Wine (Session 2026-07-09, Reckhorn DSP-6)

## Wann dieses Pattern greift

Native Windows-Apps (MFC, Win32 ohne .NET) verhalten sich unter Wine **fundamental anders** als Electron-Apps. Erkennungsmerkmale:

- **PE32 EXE ohne `mscoree.dll`-Import** (native, nicht .NET)
- **PDB-Pfad mit `\\AMPLIVE9_20120606\\Release\\...`** oder ähnlichen MFC-Build-Markern
- **Klassen-Namen wie `CDspCtlThread`, `CDialogEx`, `CMainFrame`** in den EXE-Strings
- **DLLs**: `comctl32.dll`, `comctl32.dll`, `gdi32.dll`, `gdiplus.dll`, `ole32.dll` (MFC-Stack)
- **KEIN `mscoree.dll`, KEIN `mscorlib.dll`, KEIN `dotnet`**

## 5-Schritte-Diagnose für "App startet aber Main-Window bleibt 1x1"

### Schritt 1: Memory-Map des Prozesses analysieren

```bash
# Welche DLLs sind im Memory?
PID=$(pgrep -af "<app>.exe" | head -1 | awk '{print $1}')
cat /proc/$PID/maps | grep -oE "/[^ ]+\.(dll|exe)" | sort -u
# → zeigt .NET (mscoree, mscorlib) vs native (comctl32, gdi32, user32)
# → zeigt Treiber-DLLs (SiUSBXp, ftd2xx, etc.)
```

Native MFC Apps laden typisch:
- `comctl32.dll`, `comctl32.dll`, `comdlg32.dll`, `gdi32.dll`, `gdiplus.dll`
- `ole32.dll`, `oleaut32.dll`, `oleacc.dll`
- `shell32.dll`, `shlwapi.dll`, `shcore.dll`
- `user32.dll`, `imm32.dll`, `uxtheme.dll`
- `winmm.dll`, `version.dll`, `ws2_32.dll`
- `kernel32.dll`, `kernelbase.dll`, `ntdll.dll`

NICHT in der Liste: `mscoree.dll`, `mscorlib.dll`, `wpfgfx_*.dll`, `PresentationCore.dll`

### Schritt 2: X11-Windows klassifizieren

```bash
DISPLAY=:1 xdotool search --class "<app-class>"  # z.B. "reckhorn dsp-6.exe"
# → 5 Windows typisch: 1 Main + 4 Helper (IME, Tooltips, Toolbars)

# Welche sind Main-Windows vs Helper?
for wid in $(DISPLAY=:1 xdotool search --class "<app-class>"); do
  echo "--- $wid ---"
  DISPLAY=:1 xwininfo -id "$wid" 2>&1 | grep -E "Width|Height|Map State"
done
# Main-Window:  IsViewable + sichtbare Geometrie (oder 1x1 bei USB-Wait)
# Helper-Windows: IsUnMapped (interne, nicht sichtbar)
```

### Schritt 3: USB-Hardware-Wait-Check (häufige Ursache)

```bash
# DLLs im Memory: Treiber-DLL = wartet auf Device
cat /proc/$PID/maps | grep -iE "usb|serial|si" | grep -oE "/[^ ]+\.(dll|so|sys)" | sort -u
# SiUSBXp.dll = SiLabs USBXpress (z.B. Reckhorn, viele Audio-DSP)
# ftd2xx.dll = FTDI (häufig für USB-Serial-Geräte)
# libusb*.so = generische libusb

# Falls Treiber-DLL geladen: App wartet auf USB-Device
# → lsusb | grep <vendor:product>
# → modprobe usbserial vendor=0x10c4 product=0xea60
```

### Schritt 4: Wine-Virtual-Desktop aktivieren (Workaround)

```bash
# Setzt einen 1280x800 Container-Bereich
WINEPREFIX=/path/to/bottle wine reg add 'HKCU\Software\Wine\Explorer\Desktops' /v Name /d Default /f
WINEPREFIX=/path/to/bottle wine reg add 'HKCU\Software\Wine\Explorer\Desktops' /v Width /d 1280 /f
WINEPREFIX=/path/to/bottle wine reg add 'HKCU\Software\Wine\Explorer\Desktops' /v Height /d 800 /f
```

**Limitierung:** Das setzt nur den Container, NICHT die Window-Geometrie. Helper-Windows
orientieren sich daran, Main-Windows mit `WS_POPUP` machen was sie wollen.

### Schritt 5: Auto-Geometrie-Fix im Python-Wrapper

```python
def fix_window_geometry():
    """Resize Helper-Windows via wmctrl, ignore Main (WS_POPUP)."""
    display = os.environ.get("DISPLAY", ":1")
    w, h, x, y = 1024, 768, 200, 150

    for _ in range(30):  # 30s warten
        r = subprocess.run(
            ["xdotool", "search", "--class", "<app-class>"],
            env={**os.environ, "DISPLAY": display},
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            wm = subprocess.run(
                ["wmctrl", "-l", "-G"],
                env={**os.environ, "DISPLAY": display},
                capture_output=True, text=True, timeout=5,
            )
            for line in wm.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 7:
                    try:
                        wid = parts[0]
                        cur_w, cur_h = int(parts[5]), int(parts[6])
                        if cur_w < 200 or cur_h < 200:
                            # Klein → wahrscheinlich Helper oder 1x1-Main
                            subprocess.run(
                                ["wmctrl", "-i", "-r", wid, "-e", f"0,{x},{y},{w},{h}"],
                                env={**os.environ, "DISPLAY": display},
                                capture_output=True, timeout=5,
                            )
                    except (ValueError, IndexError):
                        pass
        time.sleep(1)
```

## Warum Main-Windows sich NICHT resized bekommen (technisch)

`WS_POPUP`-Style Windows haben **keinen System-Rahmen** und keinen Resize-Handler, der
externe `WM_SIZE`-Messages akzeptiert. Der App-Code subscribed explizit auf `WM_SIZE`
in der WindowProc und:

1. Ignoriert die neue Größe, oder
2. Re-rendert das interne Layout, was die externe Größe auf 1x1 zurücksetzt

MFC Apps die `CW_USEDEFAULT` mit `WS_POPUP` benutzen, kalkulieren die initiale Größe
oft basierend auf `GetSystemMetrics(SM_CXSCREEN)` — was unter Wine oft 1 oder 0 zurückgibt.

**Workarounds (alle umständlich):**
1. **App-Quellcode patchen** — nicht möglich bei Closed-Source
2. **DX11/WinRT-App mit WS_OVERLAPPED bauen** — geht nicht für bestehende Apps
3. **Wine-Patch für `GetSystemMetrics`** — experimentell, kann andere Apps brechen
4. **Hardware anschliessen** — wenn App auf USB-Wait, löst das das Main-Window

## Visuelle Verifikation wenn App mit 1x1-Window "läuft"

`xwd` ist die **einzige zuverlässige** Screenshot-Methode für Wine-Fenster auf Wayland
(weil `scrot`/`import` den ganzen Desktop oder nichts capturen):

```bash
# Screenshot eines Wine-Windows als XWD-Dump
DISPLAY=:1 xwd -id 0x03e00003 -out /tmp/wine-window.xwd
convert /tmp/wine-window.xwd /tmp/wine-window.png
# → Wenn Window sichtbar: PNG hat 952x983 oder ähnlich
# → Wenn Window 1x1: PNG ist 1x1 (aber konvertiert erfolgreich)
file /tmp/wine-window.png
# Output: PNG image data, 952 x 983, 1-bit grayscale, non-interlaced
```

**1-Bit Grayscale** ist normal für XWD-Output (XWD speichert nicht in RGB).

## Warum Helper-Windows resized werden können, Main aber nicht

| Window-Typ | Map State | Style | Resize-Verhalten |
|---|---|---|---|
| Main (App-Hauptfenster) | IsViewable | WS_POPUP (kein Border) | Ignoriert externen Resize, nutzt interne Layout-Berechnung |
| Helper (IME, Tooltips) | IsUnMapped | WS_POPUP, WS_DISABLED | Folgt externem Resize, da kein eigener Layout-Handler |
| Default IME | IsViewable | WS_OVERLAPPED (echter Frame) | Resized immer extern |

**Workaround:** Wenn Helper-Windows resized werden und Main nicht, **ist es fast
sicher ein `WS_POPUP | WS_VISIBLE` mit internem Resize-Loop oder USB-Wait-Block**.

## MFC-App-Manifest in Bottles

Falls du Bottles als Flatpak nutzt, brauchst du für native MFC-Apps:

```bash
# NVIDIA-GL-Override (MFC nutzt oft OpenGL oder Direct3D)
flatpak override --user --env=FLATPAK_GL_DRIVER=nvidia com.usebottles.bottles
flatpak override --user --socket=x11 com.usebottles.bottles
flatpak override --user --nosocket=wayland com.usebottles.bottles
```

Plus die Wine-Runner-Empfehlung aus `references/windows-apps-on-linux.md`:
- `kron4ek-wine-11.11-amd64` für MFC-Apps die neuere Win-APIs brauchen
- `wine-ge-proton8-26` crasht bei `GetProcessInformation` (Win11-API fehlt in Wine 8)

## Bekannte Apps die dieses Pattern matchen

| App | Hersteller | DLL-Treiber | USB-Wait? | Andere Clues |
|---|---|---|---|---|
| Reckhorn DSP-6 V3.3 | SoundMagus (Reckhorn) | SiUSBXp.dll | Ja (DSP-6 mini USB) | PDB: `\\AMPLIVE9_20120606\Release\SOUNDMAGUS DSP Utility.pdb` |
| Behringer Device-Editor | Behringer | usbwin.sys (umgelabeltes SiUSBXp) | Ja | MIDI-Audio-Geräte |
| MiniDSP-Plug-ins | MiniDSP | FTDI-DLL | Ja (USB-DSP) | FTDI-VID 0x0403 |
| TC Electronic-Editor | TC Electronic | Custom WinUSB | Ja | ASIO-Treiber erforderlich |

Alle haben: **Haupt-EXE öffnet sich erst nach USB-Device-Erkennung.**

## Test mit echter Hardware

```bash
# 1. USB-Device anschliessen
# 2. Vendor/Product checken
lsusb | grep -i "silab\|ftdi\|winusb"
# 3. Linux-Kernel-Treiber laden
sudo modprobe usbserial vendor=<vid> product=<pid>
sudo chmod 666 /dev/ttyUSB*
# 4. App starten
reckhorn-dsp-6
# 5. Warten auf "Connect device"-Splash → wechselt zu Main-Window
# 6. Screenshot via xwd
DISPLAY=:1 xwd -id <main-window-id> -out /tmp/dsp6.xwd
convert /tmp/dsp6.xwd /tmp/dsp6.png
```

Wenn Main-Window sich nach Device-Connect öffnet: **Setup ist verifiziert**.
Wenn nicht: tieferes Reverse-Engineering der App nötig (PDB-Symbole, IDA Pro, Ghidra).

## Lessons Learned

1. **Native MFC ≠ Electron** — andere DLLs im Memory, andere Window-Klassen, andere
   Resize-Mechanik. Pattern 5 in `wine-electron-apps` deckt nur Electron ab.
2. **`WS_POPUP` + `WM_SIZE`-Handler = externer Resize unmöglich** — ist App-Architektur,
   nicht Wine-Bug. Workarounds sind alle hässlich.
3. **USB-Hardware-Detection ist die häufigste Ursache für 1x1-Main-Windows** bei
   Device-Configuration-Tools. Treiber-DLL im Memory + keine sichtbare UI = wartet auf Device.
4. **Helper-Windows resized ja, Main-Window nein** = asymmetrisches Verhalten weil Helper
   passive Win32-Windows sind, Main eine eigene `WindowProc` hat
5. **xwd-Screenshots funktionieren wenn alles andere versagt** — letzte Option für visuelle
   Verifikation, gibt 1-Bit-PNG aus (trotzdem aussagekräftig wenn Window-Inhalt da ist)
6. **PDB-Strings sind die schnellste Identifikations-Methode** — `strings` + PDB-Pfad-Pattern
   verrät App-Identität, Build-Datum, Build-Environment in 5 Sekunden
7. **Klassen-Namen-Heuristik**: `CMFCToolBars...` = MFC, `CDspCtlThread` = Device-Thread,
   `DSPUtilityApp` = Hauptapp. Klassenamen verraten Architektur.
