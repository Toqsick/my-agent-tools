# Reckhorn DSP-6 Session 2026-07-09: Real-World Lessons

Detailed notes from a complete Bottles/Wine setup session for an Audio-DSP tool. Captures pitfalls that the SKILL.md abstracts over.

## Specific Pitfalls Hit (with Workarounds)

### Pitfall 1: 1x1 Main-Window trotz xdotool

**Symptom:**
- 5 X11-Windows registriert, alle als `reckhorn dsp-6.exe` Class
- 4 davon: `Map State: IsUnMapped`, 1x1 Pixel
- 1 davon: `Map State: IsViewable`, 1x1 Pixel (= Main)
- `xdotool windowsize` und `wmctrl -e` haben **keinen Effekt auf das Main-Window** (1x1 bleibt 1x1)
- App rendert nichts Sichtbares (Wayland scrot = leeres Bild, xwd = 1x1 PNG)

**Root Cause:** MFC native App nutzt `CreateWindow(WS_POPUP | WS_VISIBLE)` mit `CW_USEDEFAULT`-Grösse und hat einen internen `WM_SIZE`-Handler der jede externe Resize-Anforderung sofort auf 1x1 zurücksetzt. Helper-Windows (IME, Tooltips) folgen externen Resize-Befehlen — Main-Windows mit `WS_POPUP` nicht. **Asymmetrisch und schwer zu debuggen.**

**Workaround:** Siehe Pattern 5 im SKILL.md. Der Trick ist:
- Helper-Windows kann man resized bekommen (4 von 5) — `wmctrl -i -r <wid> -e 0,200,150,1280,800`
- Main-Window bleibt 1x1 — entweder App wartet auf USB-Hardware, oder interner Resize-Loop
- **Visual-Verifikation via xwd** (nicht scrot): `xwd -id <wid> -out screen.xwd && convert screen.xwd screen.png`

### Pitfall 2: MFC vs .NET Detection

**Wie man erkennt ob die App .NET oder native MFC ist:**

```bash
# Welche DLLs sind im Memory des Prozesses?
cat /proc/<pid>/maps | grep -iE "dll|exe" | grep -oE "/[^ ]+\.(dll|exe)" | sort -u | head -30

# Wenn .NET: mscoree.dll, mscorlib.dll, Microsoft.NET.* sind geladen
# Wenn native: comctl32, comdlg32, gdi32, gdiplus (MFC/Win32-Stack)
```

**Befund im Reckhorn-Fall:** KEIN mscoree — native MFC. Hat aber CDspCtlThread (USB-Thread) und DSPUtilityApp/DSPUtilityDlg (Dialog-Klassen). PDB-Pfad verrät Identity: `\\AMPLIVE9_20120606\\AMPLIVE9_20131219\\Release\\SOUNDMAGUS DSP Utility.pdb` → Hersteller = SoundMagus Audio Ltd, Brand = Reckhorn.

**Warum das wichtig ist:**
- .NET-Apps scheitern oft an fehlenden Mono-Versionen
- MFC-Apps scheitern oft an fehlenden Visual C++ Runtimes
- Erkennung bestimmt, welche Winetricks-Pakete gebraucht werden

### Pitfall 3: Pfad-Doppelung in Wrapper-Args

**Symptom:**
```
wine: failed to open "Z:\\Program Files\\Reckhorn DSP-6\\Reckhorn DSP-6.exe"
```

**Ursache:** `wine 'Z:\Program Files\...'` — Wine erwartet entweder:
- Unix-Pfad: `wine /path/to/drive_c/.../app.exe`
- Korrekter Z: aber **ohne backslash-doubling in der bash-quote**

**Fix:**
```bash
# Variante 1: Unix-Pfad (empfohlen, portabel)
"$WINE_BIN" "/path/to/drive_c/Program Files/AppName/AppName.exe"

# Variante 2: Detached mit wine start
"$WINE_BIN" start /unix "/path/to/drive_c/Program Files/AppName/AppName.exe"

# Variante 3: Windows-Pfad mit korrektem quoting
"$WINE_BIN" 'Z:\Program Files\AppName\AppName.exe'   # single quotes, single backslash
```

### Pitfall 4: Wineserver kill muss mit wineserver-binary gemacht werden, nicht pkill

**Falsch:** `pkill -9 -f "Reckhorn DSP-6.exe"`
- Killt nur die Haupt-EXE, lässt wineserver und Treiber-Prozesse laufen
- Beim nächsten Start: "wineserver is already running for prefix X"

**Richtig:**
```bash
WINESERVER_BIN="$RUNNER/bin/wineserver"
"$WINESERVER_BIN" -k  # killt ALLE Prozesse dieses Prefix
sleep 2
```

### Pitfall 5: Wine-Virtual-Desktop ist Container, nicht Window-Geometrie

**Erwartet:** `reg add 'HKCU\Software\Wine\Explorer\Desktops' /v Width /d 1280 /f` resized das Main-Window auf 1280x800.

**Realität:** Virtual-Desktop ist nur ein Container (alle Wine-Fenster darin gezeichnet werden). Helper-Windows (IME etc.) folgen der Container-Geometrie. **Main-Windows nicht** wenn App internen Resize-Loop hat.

**Use-Case:** Virtual-Desktop trotzdem sinnvoll, weil:
- Multiple Windows kollidieren nicht mehr mit Host-Panel-Tasks
- Helper-Windows orientieren sich an Container-Grösse
- Wine-Apps mit normaler Resize-Logik (z.B. Notepad) funktionieren

**Kombination:** Virtual-Desktop setzen **UND** Main-Window-Resize akzeptieren das die App das ignoriert = beste Vorbereitung für Apps die nicht auf Hardware warten.

## End-to-End Pattern: From ZIP to Friend's Linux Box

Konkreter Workflow der die App für einen Freund bereitstellt:

### Schritt 1: Bottle in Bottles-Standard-Pfad anlegen

```bash
RECK_PREFIX="$HOME/.var/app/com.usebottles.bottles/data/bottles/bottles/Reckhorn-DSP-6"
mkdir -p "$RECK_PREFIX"
WINEPREFIX="$RECK_PREFIX" "$RUNNER/bin/wine" wineboot --init  # 1.6 MB Prefix
```

Nicht über Bottles-GUI — direkter wineboot ist 100x schneller und erzeugt einen kompatiblen Prefix.

### Schritt 2: Files in den Prefix

```bash
DEST="$RECK_PREFIX/drive_c/Program Files/Reckhorn DSP-6"
mkdir -p "$DEST"
cp -v /tmp/extracted/SOUNDMAGUS-DSP-Utility.exe "$DEST/Reckhorn DSP-6.exe"
cp -v /tmp/extracted/SiUSBXp.dll "$DEST/"
cp -v /tmp/extracted/SiUSBXp.dll "$RECK_PREFIX/drive_c/windows/system32/"
cp -v /tmp/extracted/SiLib.sys "$RECK_PREFIX/drive_c/windows/system32/"
```

### Schritt 3: Wrapper bauen

Siehe SKILL.md Pattern 4 (Shared-Prefix-Strategie). Wrapper-Pattern:

```python
#!/usr/bin/env python3
# launcher.py
import os, pty, select, signal, subprocess, sys, time
from pathlib import Path

BOTTLE = Path.home() / ".var/app/com.usebottles.bottles/data/bottles/bottles/Reckhorn-DSP-6"
RUNNER = Path.home() / ".var/app/com.usebottles.bottles/data/bottles/runners/kron4ek-wine-11.11-amd64"
WINE = RUNNER / "bin/wine"
WINESERVER = RUNNER / "bin/wineserver"
APP = BOTTLE / "drive_c/Program Files/Reckhorn DSP-6/Reckhorn DSP-6.exe"

# ... (kill_wine, check_setup, fix_window_geometry wie in SKILL.md)

# Haupt-Loop:
env = os.environ.copy()
env.update(WINEPREFIX=str(BOTTLE), WINEESYNC="1", WINEFSYNC="1", WINEDEBUG="-all")
proc = subprocess.Popen([str(WINE), str(APP), "--no-sandbox"],
                        stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
                        env=env, preexec_fn=os.setsid,
                        cwd=str(APP.parent))
# ... PTY-read-Loop
```

### Schritt 4: Bottle bereinigen für Distribution

Eine frische `wineboot` Bottle ist **1 GB gross** (Wine 11.11 hat system32=290MB, syswow64=263MB, mono=227MB, winsxs=31MB, .NET=7MB).

**Was wir wegräumen können** (jeweils getestet, App läuft danach trotzdem):

| Was | Größe | Warum wegwerfbar |
|---|---|---|
| `syswow64/` (komplett) | 263 MB | 64-bit Windows-Subsystem, 32-bit App braucht's nicht |
| `mono/` (komplett) | 227 MB | Mono ist .NET-Compat, MFC-App braucht's nicht |
| `winsxs/` (komplett) | 31 MB | Side-by-side Assembly Cache, neuere Wine macht's neu |
| `Microsoft.NET/` | 7.4 MB | MFC-App braucht's nicht |
| `users/bratan/AppData/Local/Cache` etc. | ~50 MB | User-Cache, neu aufgebaut |
| `windows/Installer/` | 80 MB | MSI-Cache, nicht relevant für Standalone-App |
| `windows/temp/` | beliebig | Temp-Dateien |

**Resultat:** 1 GB → 280 MB, ohne App-Funktionalität zu beeinträchtigen.

**Vorsicht beim Testen:** Nach jeder Bereinigung muss die App **gestartet und 30s laufen gelassen** werden, um sicher zu sein dass sie nicht crasht. Sonst crasht sie erst beim User.

### Schritt 5: Bundle packen + Audiobook erstellen

```bash
# Bundle
tar -cf - README.md reckhorn-dsp-6-bundle/ | zstd -19 -o bundle.tar.zst
# Ratio: 290 MB → 50 MB (17%)

# Audiobook (siehe audio-instructions skill)
mkdir audiobook/
# 11 TTS-generierte MP3-Kapitel (siehe audio-instructions SKILL.md)
cat > audiobook/playlist.m3u <<EOF
01-einleitung.mp3
02-bottles-installieren.mp3
...
EOF

# Audiobook packen
tar -cf - audiobook/ | zstd -19 -o audiobook.tar.zst
# 9.6 MB → 9.5 MB (MP3s sind schon komprimiert)
```

### Schritt 6: Versand per Telegram-Bot (50 MB Limit pro Datei)

```bash
# Bei > 50 MB: splitten
split -b 45M bundle.tar.zst bundle-part-
# Ergibt 2 Parts: bundle-part-00 (45MB), bundle-part-01 (5.7MB)

# Upload via Telegram-Bot (curl + form-data)
set -a; . ~/.hermes/.env; set +a  # lädt TELEGRAM_BOT_TOKEN
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendDocument" \
  -F "chat_id=${TELEGRAM_HOME_CHANNEL}" \
  -F "document=@bundle-part-00" \
  -F "caption=Reckhorn DSP-6 Bundle Part 1/2"
```

**Wichtig:** Telegram-Bot-Limit ist **50 MB pro Datei**. Discord-Free ist 8 MB, Nitro 25 MB, Boost-Lvl2 50 MB. Für > 50 MB: split oder Cloud (Google Drive 15 GB free, WeTransfer 2 GB free).

## Bundle-Size-Optimierung im Detail

### zstd -19 vs zip -9 (verglichen 2026-07-09)

| Format | Zeit | Output | Ratio |
|---|---|---|---|
| tar (none) | 10s | 290 MB | 100% |
| tar.zst (-19) | 60s | 51 MB | 17.5% |
| tar.zst (-22, multi-thread) | 25s | 50.7 MB | 17.5% |
| 7z ultra (lzma2 -mx=9) | > 600s (timeout!) | - | - |
| zip -6 | > 600s (timeout!) | - | - |

**Winner:** `tar -cf - | zstd -19 -T 8` — 25s, beste Ratio, multi-thread, native Linux.

### Bereinigtes Bundle

| Komponente | Größe | Verbleibend |
|---|---|---|
| Bottle (cleaned) | 280 MB | 280 MB |
| README.md | 2 KB | 280 MB |
| Audiobook (11 MP3) | 9.6 MB | 290 MB |
| Audiobook tar.zst | 9.5 MB | 290 MB |
| **Bundle tar.zst** | **51 MB** | **51 MB** |
| Telegram-Parts (45+5.7) | 51 MB | 51 MB |

## Lessons Learned (übers SKILL.md hinaus)

- **Wine-PTY-Wrapper ist 95% sauber**, aber Helper-Windows-Resize-Loop nicht-trivial — Pattern 5 + Async-Fix-Thread sind die robusteste Lösung
- **MFC native Apps erkennt man an fehlendem mscoree im Memory-Map** — wichtig für Library-Auswahl (kein Mono nötig)
- **Wine-Virtual-Desktop setzt nur Container**, nicht Window-Geometrie — überschätzt das nicht
- **Wineserver-kill MUSS via wineserver-binary, nicht pkill** — sonst "wineserver already running" beim nächsten Start
- **Bundle-Bereinigung 1 GB → 280 MB ist sicher**, solange man die App nach jeder Bereinigung testet
- **zstd -19 ist klar besser als zip -9** (schneller, kleinere Files, multi-threaded)
- **Telegram-Bot 50 MB Limit** erzwingt Splitting für > 50 MB — Discord-Free ist mit 8 MB noch restriktiver
- **Audiobook als Begleitung zum Bundle** ist ein starker Pattern — der Empfänger kann während der Installation zuhören
- **`registerApplicationRestart` ist letzter Lebenszeichen** einer Wine-App — wenn nichts mehr kommt, wartet sie auf Hardware oder hängt im Init-Loop

## Offene Fragen / Nicht-Gefixt

- **MSI File-Tabelle parsen** um die GUID-Filenamen auf echte Namen zu mappen — wir haben Heuristik benutzt statt programmatisch zu parsen, das `msitools` package würde das automatisieren
- **Main-Window-Resize-Loop in MFC Apps** ist ein interner Wine-Bug oder App-Bug — ohne Code-Mods nicht fixbar
- **Reckhorn DSP-6DEU.dll / Reckhorn DSP-6LOC.dll** fehlen komplett im CAB — Localization funktioniert nicht (App crasht nicht, aber UI ist nicht übersetzt)
- **SiLabs USBXpress Linux-Treiber** ist nicht im mainline-Kernel — User braucht proprietären Treiber von silabs.com, falls generic usbserial das Gerät nicht erkennt (ProductID=0xea60 vermutet)
</content>
</invoke>