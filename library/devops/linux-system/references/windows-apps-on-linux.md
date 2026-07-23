# Windows Desktop Apps auf Linux — Installation & Troubleshooting

> Vollständige Anleitung zu Installer-Formaten, Wine vs Bottles vs Web-Alternative,
> mit Fokus auf Electron-Apps, NSIS/7z-Handling und Entscheidungsfindung.

## Installer-Formate erkennen und entpacken

| Format | `file`-Ausgabe | Tool | Befehl |
|--------|---------------|------|--------|
| **NSIS (Nullsoft)** | `PE32 ... Nullsoft Installer ...` | `7z` | `7z x setup.exe -o./extracted` |
| **Inno Setup** | `PE32 ... Inno Setup` | `innoextract` | `innoextract setup.exe -d ./extracted` |
| **InstallShield** | `cabarc` / `ISSetup.dll` | `unrar` + `cabextract` | `unrar x setup.exe && cabextract *.cab` |
| **WiX (MSI)** | `Composite Document File V2` / `.msi` | `msiextract` | `msiextract setup.msi` (msitools: `sudo apt install msitools`) |
| **Portable EXE** | `PE32 ... console/GUI` | `wine` | `wine program.exe` |

### Ein-Befehl-Identifikation

```bash
file "setup.exe" && \
  7z l setup.exe 2>/dev/null | head -5 && \
  echo "---" && \
  echo "Erkannt als: $(file -b setup.exe | grep -oE \
    '(Nullsoft|Inno|InstallShield|PE32 (GUI|console)|MSI|Portable)')"
```

### NSIS-Installation — Silent vs. Manuell

**Silent (Dateisystem schreibt direkt):**
```bash
wine setup.exe /S /D=C:\\Programme\\AppName
```
⚠️ **Pitfall:** Silent-Install (`/S`) hängt bei Electron-NSIS-Installern unter Wine wenn der
Installer den Electron-Updater vor dem eigentlichen Setup initialisiert (Node EBADF).
Timeout nach 2-3 Minuten → Exit-Code 2 (Fehler beim Entpacken).
→ Dann IMMER manuelle Extraktion mit 7z.

**Manuell (Installer extract + app im extracted-Ordner starten):**
```bash
7z x setup.exe -o./extracted
cd ./extracted
# Suche app-64/ oder die .exe:
find . -name "*.exe" -not -name "uninstall*" -not -path "*/System/*" | head -10
wine ./app-64/AppName.exe
```

**NSIS Archive-in-Archive Pattern:** Je nach Build-Version liegt das Electron-Bundle
entweder als Verzeichnis ODER als gepackte `.7z` Datei im `$PLUGINSDIR`:
```bash
# Variante A: bereits entpackt (MiniMax Hub 1.0.7)
mkdir -p extracted && cd extracted
7z x setup.exe
ls "\\$PLUGINSDIR/app-64/"    # → AppName.exe + resources/

# Variante B: als app-64.7z (MiniMax Code 3.0.47 — NSIS 3.04 Build)
7z x setup.exe
7z x "\\$PLUGINSDIR/app-64.7z" -o./app64
# → 6 Warnungen "Dangerous link path was ignored" für Mac-Build-Container-Symlinks
#   (unter Wine irrelevant, symlinks existieren nicht in NTFS-Filesystem)
```
**Shell-Hinweis:** `$PLUGINSDIR` enthält ein `$` — im Terminal mit Backslash escapen
(`\$PLUGINSDIR`) oder in einfache Anführungszeichen setzen (`'$PLUGINSDIR'`).

## "Web first, Wine second" — Entscheidungsstrategie

Bevor du mit Wine/Bottles Zeit verbringst:

1. **Gibt es eine Web-Version der App?** → Browser öffnen, sofort testen.
2. **Gibt es eine native Linux-Version?** → AppImage, Flathub (flatpak), Snap.
3. **Ist die App pure API-getrieben?** → API-Key holen, via curl/CLI nutzen.
4. **Erst dann: Wine oder Bottles.**

### Fallbeispiel: MiniMax Hub (HailuoAI)

- **Web-Suite:** `hailuoai.video/create` — Video, Image, Audio Gen, Asset-Tools laufen sofort im Browser.
- **Desktop-Only-Features:** "Hub"-Tab (Multi-Agent-Orch) + Local-File-Assets sind Desktop-exklusiv.
- **Auf Linux:** `file` -> "Nullsoft Installer" -> `7z x` entpackt in `app-64.7z` + `nsis_extra` + `embedded`.
- **NSIS+7z-Trick:** NSIS-Installer enthalten die App oft in einem `.7z`-Archiv:
  ```
  7z x setup.exe -o./extracted
  find ./extracted -name "*.7z"    # app-64.7z finden
  7z x ./extracted/app-64.7z -o./app
  wine ./app/AppName.exe           # direkt starten
  ```
- **Fazit:** ~70% der Funktionen im Browser. Desktop nur wenn Multi-Agent-Arbeitsfluss wirklich noetig.

## Bottles Flatpak auf NVIDIA - Spezielle Fallstricke

Wenn Bottles als Flatpak auf einem NVIDIA-System laeuft, koennen NVIDIA-Treiber-Libs im Sandbox unsichtbar sein.

### Symptome im Bottles-Journal

```
~/.var/app/com.usebottles.bottles/data/bottles/journal.yml:
  Unable to load libGLX_nvidia.so.0
  Unable to locate libGLX_nvidia
```

**Ursache:** Flatpak-Sandbox isoliert die Host-Grafiktreiber. NVIDIA-GLX-Libs sind fuer Wine-Prozesse nicht erreichbar -> Installationsabbrueche oder schwarzer Bildschirm.

### Fix 1: NVIDIA-GL-DRIVER Flatpak-Override (BEVOR die Bottle startet)

```bash
# Zwingt Bottles, die NVIDIA-GL-Extension zu mounten statt Mesa-Fallback
flatpak override --user --env=FLATPAK_GL_DRIVER=nvidia com.usebottles.bottles
flatpak override --user --socket=x11 com.usebottles.bottles
flatpak override --user --nosocket=wayland com.usebottles.bottles
```

**Verifikation:** Wenn Bottles startet und `~/.var/app/com.usebottles.bottles/cache/nvidia/GLCache/` beschrieben wird, läuft die GL-Pipeline über NVIDIA-Treiber.

### Fix 2: Runner-Auswahl (KRITISCH für moderne Electron-Apps)

| Runner | Wine | NVIDIA-GL | Moderne Electron-Apps | Empfehlung |
|--------|------|-----------|----------------------|-----------|
| `wine-ge-proton8-26` | 8.0-Staging | ✅ | ❌ **Crasht bei `KERNEL32.GetProcessInformation`** | Nur alte Spiele |
| `caffe-9.7` | TkG 9.7 | ⚠️ | ❌ Selbe Lücke | Legacy |
| `soda-9.0-1` | 9.0 | ❌ | ❌ Zu alt | Default, schlecht für Electron |
| `kron4ek-wine-11.11-amd64` | **11.11** | ✅ | **✅ Funktioniert** | ⭐ **Erste Wahl für Electron** |

**Lektion 2026-07-03 (MiniMax Hub):** `wine-ge-proton8-26` crasht moderne Electron-Apps bei `kernel32!GetProcessInformation` (Win11-API fehlt in Wine 8.x). Bei Electron-Apps auf NVIDIA IMMER `kron4ek-wine-11.11-amd64` (Wine 11+) verwenden.

**Runner-Wechsel per CLI (ohne GUI):**
```bash
BOTTLE=~/.var/app/com.usebottles.bottles/data/bottles/bottles/<name>
sed -i 's/^Runner:.*/Runner: kron4ek-wine-11.11-amd64/' "$BOTTLE/bottle.yml"
WINEPREFIX=$BOTTLE ~/.var/app/com.usebottles.bottles/data/bottles/runners/kron4ek-wine-11.11-amd64/bin/wineboot -u
```

**Runner-Wechsel per Bottles GUI (falls CLI nicht gewünscht):**
1. Bottles starten -> Bottle auswaehlen -> Zahnrad (Einstellungen)
2. Tab "Runner & Runtime"
3. Runner-Dropdown: `kron4ek-wine-11.11-amd64` auswaehlen
4. Bottle schliessen und neu starten

### `bottles-cli` Einschraenkung

Kann **nicht von aussen** (ausserhalb Flatpak-Sandbox) aufgerufen werden:
```bash
# ❌ Crasht:
bottles-cli --help
# -> ModuleNotFoundError: No module named 'bottles'
# -> ModuleNotFoundError: No module named 'pycurl'

# ✅ Geht so:
flatpak run --command=bottles-cli com.usebottles.bottles <args>
```
Die CLI braucht Python 3.13 + pycurl im Flatpak-Kontext, die von aussen nicht verfuegbar sind.

### Bekannte Einschraenkungen (Bottles 64+)

- `use_system_runtime` (Host-Wine-Modus) wurde **entfernt**
- NVIDIA-GLX-Probleme treten nur im Flatpak-Sandbox auf, nicht bei nativem Wine
- `bottle.yml`+Tarball-Backups enthalten **nie** die installierte App

## Electron-Apps unter Wine — Spezielle Fallstricke

Electron-Apps sind **keine Spiele**: Proton bringt nix, Wine hat harte Einschränkungen. Drei nicht-offensichtliche Killerprobleme sind unten dokumentiert.

### Tabelle der typischen Probleme

| Feature | Unter Wine | Problem |
|---------|-----------|---------|
| Auto-Update (`electron-updater`) | ❌ Oft defekt | Squirrel.Windows-Pipeline fehlt |
| OAuth-Login (Google/GitHub) | ⚠️ Hängt oft | Browser-Fenster öffnet falsch |
| Local-FS-Zugriff | ⚠️ Eingeschränkt | `C:\\` = `~/.wine/drive_c/`. Rest via symlink |
| CUDA/Hardware-Encode | ❌ Nicht verfügbar | GPU-Compute fehlt meist |
| GPU-Compositing | ⚠️ Langsamer | SwiftShader fallback statt native GPU |
| System-Tray/Notification | ❌ Oft kaputt | DBus/Wayland fehlt |
| **Node.js Stdio (siehe unten)** | ❌ **App crashed sofort** | EBADF ohne TTY |
| **Win11-API-Lücke (siehe unten)** | ❌ **Wine 8.x crashed** | `GetProcessInformation` etc. fehlt |

### Killer-Pitfall #1: Node.js Stdio EBADF (Electron-Apps starten nicht)

**Symptom:** Electron-App crashed sofort mit Error-Dialog:
```
A JavaScript error occurred in the main process

Uncaught Exception:
Error: open EBADF
    at new Socket (node:net:437:13)
    at createWritableStdioStream (node:internal/bootstrap/switches/is_main_thread:83:18)
    at process.getStdout [as stderr] (node:internal/bootstrap/...)
        [OK]
```

**Ursache:** Node.js prüft beim Start, ob fd 0/1/2 echte TTYs sind. Bei Pipe-Redirect (z.B. `> /tmp/log 2>&1`, `2>&1 | tee`, Background-Prozesse) sind die fds Pipes, kein TTY → Node kriegt `EBADF` und crashed im Bootstrap.

**Fix: Python-PTY-Wrapper als Launcher (siehe `templates/electron-wine-pty-launcher.py`):**
```python
master_fd, slave_fd = pty.openpty()
proc = subprocess.Popen(
    [wine, exe, '--no-sandbox', '--disable-software-rasterizer'],
    stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
    env=env, preexec_fn=os.setsid
)
```

**Warum nicht `script -qc`?** Leerzeichen in Pfaden + Quoting-Probleme; Python-pty.openpty() ist deterministischer.

**Wann ist das NICHT nötig?** Beim manuellen GUI-Start aus Bottles selbst (Bottles spawnt die Wine-Prozesse mit ordentlichen TTYs).

### Killer-Pitfall #2: Win11-API-Lücke in alten Wine-Versionen

**Symptom:** Electron-App startet, lädt Logo-Screen, crashed 2-3 Sekunden später mit:
```
wine: Call from 0000000170030688 to unimplemented function KERNEL32.dll.GetProcessInformation, aborting
```

**Ursache:** `GetProcessInformation` ist erst seit Win10/11 in kernel32.dll. Wine 8.x (GE-Proton) hat diese API nicht — Wine 11+ schon.

**Fix:** Runner wechseln — `wine-ge-proton8-26` ist NICHT gut genug für moderne Electron-Apps, sondern `kron4ek-wine-11.11-amd64` (oder neuer).

**Verifikation:** Im Wine-Debug-Output (`WINEDEBUG=+loaddll`) taucht `GetProcessInformation` nur auf, wenn die App es auch aufruft. Wenn im Log keine `err:GetProcessInformation`-Meldung erscheint, ist alles gut.

### Killer-Pitfall #3: NSIS-Installer crashed wegen .NET-Pre-Requisiten

**Symptom:** Bottles installiert bottle.yml-Konfig, Installer-Fenster geht kurz auf und schließt sich. `drive_c/` ist leer. Im Bottles-Journal:
```
message: Component installation failed
severity: error
```

**Ursache:** Der NSIS-Installer hat internal Pre-Requisiten-Checks für .NET 4.8.1 / dotnetcore / dotnet20, die in einer frischen Wine-Bottle (ohne dotnet-Pre-Install) chicken-and-egg crashen.

**Fix: NSIS-Bundle manuell entpacken statt Installer laufen lassen:**
```bash
# 1. Setup-EXE entpacken (NSIS speichert darin alles als 7z)
mkdir -p extracted && cd extracted
7z x "../MiniMax Hub Setup 1.0.7.exe"

# 2. Electron-Bundle findet sich unter $PLUGINSDIR/app-64/
ls "\$PLUGINSDIR/app-64/"  # Haupt-EXE + DLLs + Resources

# 3. Bundle direkt in Bottle kopieren (umgeht Installer)
mkdir -p ~/.var/app/com.usebottles.bottles/data/bottles/bottles/<name>/drive_c/MiniMax-Hub
cp -r "\$PLUGINSDIR/app-64/." /home/bratan/.var/app/com.usebottles.bottles/data/bottles/bottles/<name>/drive_c/MiniMax-Hub/

# 4. VC-Redist separat installieren (Pre-Req für viele Electron-Apps)
WINEPREFIX=$BOTTLE wine "\$PLUGINSDIR/vc_redist.x64.exe" /quiet /norestart
```

### Electron-App in Bottles: Komplett-Rezept

```bash
# Schritt 1: Bottle anlegen (Runner = kron4ek-wine-11.11-amd64)
# Schritt 2: NVIDIA-Flatpak-Override setzen (siehe oben)
# Schritt 3: VC-Redist silent in Bottle installieren
# Schritt 4: App-Bundle manuell aus NSIS-Installer nach drive_c/<Name>/ extrahieren
# Schritt 5: Wine-Init mit wineboot -u
# Schritt 6: App starten via Python-PTY-Wrapper (Pitfall #1!)
```

### Sibling-App Bottle Recycling (geteiltes Wine-Prefix)

Wenn zwei Apps vom **selben Hersteller / Ökosystem** stammen (z.B. MiniMax Hub + MiniMax Code,
beides ByteDance-Electron-Apps), können sie ein Wine-Prefix teilen statt jeweils eine
eigene Bottle zu bekommen. Spart 4-5 GB pro App (kein zweiter Prefix, keine doppelten Dependencies).

**Voraussetzungen für Recycling:**
✓ Gleicher Hersteller (selbe CompanyName im Installer)
✓ Gleicher Runner (Wine-Version), getestet für App A
✓ Gleiche Abhängigkeiten (VC Redist, dotnet etc. schon installiert)
✓ App nutzt denselben Electron-Stack (erkennbar an `@hilodesktop-updater`, `app.asar`)

**Vorgehen (am Beispiel MiniMax Code + Hub in einer Bottle):**
```bash
# 1. Bundle aus NSIS-Installer extrahieren (siehe oben)
7z x setup.exe -o./extracted
7z x './extracted/$PLUGINSDIR/app-64.7z' -o./app64

# 2. Bundle in BESTEHENDE Bottle kopieren (kein wineboot!)
DEST="~/.var/app/com.usebottles.bottles/data/bottles/bottles/EXISTING-BOTTLE/drive_c/MiniMax-Code"
mkdir -p "$DEST"
cp -r ./app64/. "$DEST/"

# 3. PTY-Wrapper bauen (selbe Wine-Runner-Pfade, nur APP_EXE anpassen)
# 4. Desktop-File für App B erstellen
# 5. Test-Start + Heartbeat-Verifikation (siehe oben)
```

**Pitfalls:**
| Risiko | Symptom | Workaround |
|--------|---------|-----------|
| Updater-Konflikt | Beide Apps schreiben in `%LOCALAPPDATA%\MiniMax Agent\` | Beim Start von App B: App A vorher beenden |
| Registry-Kollision | Beide nutzen `HKCU\Software\MiniMax\` | Separate Env-Vars erlaubt, keine Konflikte beobachtet |
| Version-Mismatch | App B braucht jüngere/ältere Wine-Version | Recycling nur wenn Wine-Version identisch |

**Lektion 2026-07-08 (MiniMax Code + Hub):** Bundle-Struktur identisch (Electron + app.asar +
dieselben Native Modules in app.asar.unpacked), Heartbeat-Endpunkt leicht verschieden
(`agent.minimax.io` vs `hailuoai.video/matrix/`) aber sonst gleiches Protokoll.
Keine Konflikte in 3h Betrieb beobachtet.

### Bessere Alternativen
- Web-Version suchen (fast immer verfügbar bei SaaS)
- Electron-App mit eigenem Chromium unter Linux starten (wenn sie als ESM/Node verfügbar)
- Flatpak-Version vom Hersteller abwarten

## Electron-Render-Diagnose: Fenster da, aber was zeigt es?

Wenn die Wine/Electron-App startet (kein Crash, keine EBADF), aber das sichtbare Fenster wirkt kaputt oder zu klein (z.B. 354×292 Error-Icon statt der Haupt-UI), liegt das fast immer am Login/OAuth-Token und nicht am Renderer.

### Werkzeugkasten: Electron-Fenster im X11-Wald finden

```bash
# 1. Welche Fenster-IDs hat die App?
DISPLAY=:1 xwininfo -root -tree 2>&1 | grep -E "<app-name>"
# → mehrere 1x1-Pseudo-Fenster (Electron IPC), und das Haupt-Fenster

# 2. Haupt-Fenster-Detail: Klasse + Größe + Map-State
DISPLAY=:1 xwininfo -id 0x4400005
#   Map State: IsUnMapped   ← Fenster wurde noch nicht gemappt!
#   Map State: IsViewable   ← sichtbar, alles gut

# 3. Screenshot des Haupt-Fensters (für visuelle Diagnose)
DISPLAY=:1 xwd -id 0x4400005 -out /tmp/window.xwd
convert /tmp/window.xwd /tmp/window.png
# xwd bricht mit "BadColor" ab wenn Fenster noch nicht gemappt — ok, dann kein Screenshot

# 4. Aktive Wine-Prozesse
pgrep -af "wine|<app-exe-name>" | head -5

# 5. Live-Log-Datei (Electron schreibt nach user-config oder AppData)
LOG=~/.var/app/com.usebottles.bottles/data/bottles/bottles/<bottle>/drive_c/users/<user>/AppData/Roaming/<vendor>/<app>/logs/main-$(date +%m-%d).log
tail -25 "$LOG"

# 6. Live-Bridge-API testen (Electron-Apps haben oft localhost:<port> IPC-Bridge)
curl -s --max-time 3 http://127.0.0.1:41609/health
curl -s --max-time 3 http://127.0.0.1:8001/
```

**Pitfall:** `pgrep -af "wine"` zeigt Prozesse — wenn die laufen, crashed die App NICHT sondern wartet meist auf Auth-Token. Das kleinere Fenster ist nur ein Modal-Overlay.

### xwd-Screenshot-Workaround für Wayland (letzte Option für Wine-Child-Windows)

`scrot`, `import -window`, `gnome-screenshot` liefern auf Wayland+XWayland **leere
oder fehlerhafte Bilder** für Wine-Child-Windows. `xwd` ist die einzige zuverlässige
Methode, gibt aber **1-Bit-Grayscale-PNG** aus (XWD-Format-Limit):

```bash
# Screenshot eines Wine-Windows (funktioniert auch für 1x1-Pseudo-Windows)
DISPLAY=:1 xwd -id <window-id> -out /tmp/window.xwd
convert /tmp/window.xwd /tmp/window.png
file /tmp/window.png
# Output: PNG image data, 952 x 983, 1-bit grayscale, non-interlaced
```

**Wann xwd scheitert:**
- `X Error of failed request: BadMatch (invalid parameter attributes)` — Window
  ist nicht mapped oder hat eine spezielle Visual-Klasse. In dem Fall: erst
  `xdotool windowraise <wid> && xdotool windowmap <wid>` und nochmal probieren.
- `X Error of failed request: BadWindow (invalid Window parameter)` — Window-ID
  existiert nicht mehr (App hat sich beendet).

**Wann xwd funktioniert:**
- Window ist mapped (`Map State: IsViewable`)
- Helper-Windows die resized wurden auf 1280x800 (typisch nach Virtual-Desktop-Set)
- Main-Window das gerade Hardware-Detection beendet hat (z.B. nach USB-Device-Connect)

**Pitfall xwd Output:** 1-Bit-Grayscale ist nicht RGB. Wenn die App nur Schwarz/Weiß
rendert, ist das visuell identisch. Bei Color-Apps (z.B. IDE-Syntax-Highlighting) gehen
Farbinformationen verloren — für Color-Screenshots vorher `xwd` mit `add-private` Option
probieren, oder in Wine-Config die `Direct3D`/GDI-Render-Pipeline prüfen.

### "Login-Modal als Hauptfenster interpretiert"-Falle

Im Screenshot-Fall MiniMax Hub zeigte sich:
- Haupt-UI = 1432×740 Electron-Renderer-Window mit korrektem App-Layout
- Login-Modal = 354×292 NAMED "Error" (Electron's Standard-Error-Dialog-Größe)
- Wenn du nur `wmctrl -l` machst und das "Error"-Fenster siehst, denkst du die App crashed — aber das Haupt-UI läuft ungestört im Hintergrund.

**Trick:** Erst `pgrep -af "wine"` + `wmctrl -lp` (zeigt PID pro Fenster). Wenn die PID gleich der wine-prozess-ID ist, lebt die App definitiv. Token-Eintrag (siehe unten) löst das Auth-Modal.

### Heartbeat-basierte Stabilitäts-Prüfung (Electron unter Wine)

Wenn die App unter Wayland startet und visuelle Screenshot-Tools (`scrot`/`import`/`xwd`)
keine Fenster-Inhalte liefern (bekannte Wayland-XWayland-Compose-Limitierung), dient
**Heartbeat-Zählen** als Proxy-Metrik für "UI läuft stabil":

```bash
LOG=/path/to/app-start-test.log

# Healthy = system-API-Heartbeat alle 6-15s
grep -c "Sent heartbeat" "$LOG"
# Erwartung: ~10+ in 3 Minuten bei stabilem Betrieb

# 5 Electron-Child-Prozesse bestätigen stabilen Start
pgrep -af "MiniMax Code\\.exe"
# → main + gpu-process + network-service + 2× renderer

# Keine Heartbeat-Lücke >60s
while read -r ts; do
  prev=$ts; # ... (sequential check)
done < <(grep -oP 'unix=\\K\\d+' "$LOG")
```

**Threshold-Werte (empirisch von MiniMax Code 3.0.47 + Wine 11.11):**
| Metrik | Gesunde App | Warnung | Crashed |
|--------|-------------|---------|---------|
| Heartbeats in 3 Min | ≥13 | 3-12 | 0 |
| Heartbeat-Intervall | 6-10 s | >30 s | — |
| Electron-Prozesse | 5 (main+gpu+network+2×renderer) | <5 | 0 |
| Wine-Prozesse | 1-2 (wineserver+wine) | wineserver nur | keiner |

**Pitfall:** Nicht alle Electron-Apps senden Heartbeats. Falls kein Heartbeat-String
im Log auftaucht → andere Proxy-Metrik suchen (`bridge-api`, `Listening on`, `ready`).

Moderner Electron-Apps haben oft eine **localhost-API-Bridge** (IPC + HTTP) — perfekte Diagnose-Sonde ohne UI-Interaktion:

```bash
# MiniMax Hub hat:
#   - main-bridge auf :41609 (Renderer → Main)
#   - gateway auf :8001 (Skill-Runtime)
# Siehe main-*.log: "[main-bridge] Listening on http://127.0.0.1:41609"
#
# Diese Bridges laufen IM Wine-Namespace ("localhost" = Wine-loopback).
# Vom Host aus NICHT direkt erreichbar — aber Hinweis dass die App lebt.
```

## Electron-Login Workaround: Token via Env-Var

Die häufigste Ursache für "App startet aber Login klappt nicht in Wine" ist, dass die Electron-App einen Browser-Popup für OAuth/QR-Code erwartet, den Wine-X11 nicht oder nur halb durchschaltet.

### Diagnose: Was will die App für Login?

Electron-Apps packen ihren Code in `app.asar` — einem read-only-Bundle. Trotzdem lässt sich die Login-Mechanik oft rekonstruieren mit simplen Unix-Tools:

```bash
# 1. Strings aus dem ASAR-Bundle extrahieren
APP_ASAR=~/.var/app/com.usebottles.bottles/data/bottles/bottles/<bottle>/drive_c/<app>/resources/app.asar
strings "$APP_ASAR" > /tmp/app-strings.txt

# 2. Login-relevante Strings finden
grep -iE 'login|auth|signin|oauth|callback|hailuoai|feishu|lark' /tmp/app-strings.txt | head -20
# → zeigt: Login-Provider (Feishu/Lark/Google/...), URLs, env-Vars die gelesen werden

# 3. Welche Token-Env-Vars akzeptiert die App?
grep -oE '([A-Z][A-Z0-9_]*_?USER_TOKEN|[A-Z][A-Z0-9_]*_?AUTH_TOKEN|ACCESS_TOKEN|API_KEY|GITHUB_TOKEN)[A-Z_]*' /tmp/app-strings.txt | sort -u
# Beobachtetes Pattern: viele Electron-Apps lesen <PROVIDER>_USER_TOKEN / <PROVIDER>_USER_TOKEN_FILE

# 4. Welche Cookie-/Token-Storage-Pfade?
grep -oE '[A-Za-z]:\\\\[^\s\'"<>]+tokens[^\s\'"<>]*' /tmp/app-strings.txt | head -5
# Häufig: globalStorage.get("tokens").accessToken

# 5. Welche Login-Provider-Endpunkte?
grep -oE 'https?://[^\s\'"<>]*(feishu|larksuite|hailuo|github|google|slack|notion|linear)[^\s\'"<>]*' /tmp/app-strings.txt | sort -u | head -10
```

**Tipp:** Wenn in den extrahierten Strings KEINE `<PROVIDER>_USER_TOKEN`-env-Var auftaucht, hat die App den Mechanismus nicht vorgesehen — dann bleibt nur Browser-Popup-Workaround oder Reverse-Engineering tieferer Schichten (sehr aufwendig).

### Bekannte Login-Provider-Mappings

| Provider | Identifier im Code | Env-Var Token-Pattern | OAuth-Popup-Domain |
|----------|---------------------|----------------------|---------------------|
| Feishu (Lark, ByteDance) | `feishu`, `lark`, `@larksuiteoapi/node-sdk` | `HILO_USER_TOKEN` | `accounts.feishu.cn` |
| GitHub | `github.com/login/oauth` | `GITHUB_TOKEN` | `github.com` |
| Google | `accounts.google.com/o/oauth2` | `GOOGLE_ACCESS_TOKEN` | `accounts.google.com` |
| Microsoft | `login.microsoftonline.com` | `MS_TOKEN` | `login.microsoftonline.com` |

### Wie kommt man an den Token?

**Browser-Methode:** Im normalen Linux-Browser (Brave/Chrome/Firefox) auf der Login-Seite einloggen:
1. DevTools öffnen (F12)
2. Tab "Application" → "Local Storage" → Domain auswählen
3. Key `access_token` / `hailuoai_token` / etc. suchen
4. Wert kopieren

**Speichern:**
```bash
echo '<HIER-DER-TOKEN>' > ~/.config/<app-name>-token
chmod 600 ~/.config/<app-name>-token
```

### Launcher-Integration

Der Launcher (`templates/electron-wine-pty-launcher.py`) muss um Token-Datei-Support erweitert werden (siehe Template):

```python
# Token-Env-Vars setzen, bevor Wine startet
token_file = Path.home() / ".config/<app-name>-token"
if token_file.exists():
    env['<PROVIDER>_USER_TOKEN_FILE'] = str(token_file)
    print(f"🔑 Token aus: {token_file}")
elif '<PROVIDER>_USER_TOKEN' not in env:
    print("ℹ️  Kein Token — Login erforderlich")
    print(f"   Token anlegen: echo '<TOKEN>' > {token_file}")
```

### Alternative: Token-Inline per Env-Var (für Einmal-Tests)

```bash
HILO_USER_TOKEN='<TOKEN>' <app-launcher>
```

## Bottles vs. Raw Wine

| Kriterium | Raw Wine | Bottles |
|-----------|----------|---------|
| Setup | `sudo apt install wine` | `flatpak install flathub com.usebottles.Bottles` |
| Konfiguration | Manuell (winecfg, regedit) | Grafisch (GUI) |
| DXVK/VKD3D | Manuelle Installation | Automatisch pro Bottle |
| Backup/Export | `tar -czf` des Prefix | `bottle.yml` + Tarball |
| Isolierte Umgebungen | Selfmade | Built-in (eine Bottle = eine App) |
| Best für | Einfache Installer (NSIS/Portable) | Komplexe Apps, Inno Setup, Electron |

### Bottles-Pitfall

Backups (`bottle.yml` + `drive_c/` Tarball) enthalten NUR:
- Wine-Konfiguration (registry, DLL overrides)
- System-DLLs und Standard-Bibliotheken
- NICHT die installierte App!

Einen `bottle.yml`-Backup-Tarball entpacken = App nicht startfähig.
Immer den originalen Installer parat halten.

### Prefix-Verwaltung (Raw Wine)

```bash
# Sauberes Prefix für eine App
WINEPREFIX=~/.wine-appname wineboot --init

# Installer drin ausführen
WINEPREFIX=~/.wine-appname wine setup.exe

# App starten
WINEPREFIX=~/.wine-appname wine "C:\Program Files\AppName\app.exe"

# Desktop-Entry
cat > ~/.local/share/applications/wine-appname.desktop << 'EOF'
[Desktop Entry]
Name=AppName
Exec=env WINEPREFIX=/home/bratan/.wine-appname wine "C:\\Program Files\\AppName\\app.exe"
Type=Application
Categories=Utility;
EOF
```

## Quick-Check vor Installation

```bash
# System ready?
wine --version
wineboot --init 2>/dev/null && echo "✅ Prefix OK"
which wine 7z innoextract cabextract msiextract

# Installer analysieren
file setup.exe

# Silent install (NSIS)
wine setup.exe /S /D=C:\Programme\AppName

# Oder entpacken + manuell starten
7z x setup.exe -o./extracted
find ./extracted -name "*.exe" -type f | head -5
```

## Bekannte Installer-Exit-Codes (NSIS)

| Code | Bedeutung |
|------|-----------|
| 0 | Erfolg |
| 1 | Abbruch durch Benutzer |
| 2 | Fehler beim Entpacken |
| 5 | Not enough privileges (kein Admin) |
| 1025 | Silent-Install-Flag fehlt (`/S`) |
| 127 | VC-Redist fehlt (`vc_redist.x64.exe` manuell installieren) |

Wenn `wine setup.exe /S` mit Exit-Code ≠ 0 endet → Manuelles Entpacken mit `7z x`
und direkter Start der App-Binary versuchen.

## Wrapper Deployment PATH Setup (dieses System)

Wrapper-Skripte in `~/50-System/bin/` werden erstellt, sind aber **nicht automatisch im `$PATH`**. Das Verzeichnis `~/.local/bin/` ist immer im PATH (über systemd-environment-generator oder ~/.profile), `~/bin/` kommt aus `~/.profile` dazu — existiert aber nur wenn das Verzeichnis auch angelegt wurde.

### Deployment-Pattern für neue Wrapper

```bash
# 1. Wrapper in 50-System/bin/ ablegen (source of truth)
# 2. Symlink in ~/.local/bin/ (primär, immer im PATH)
ln -sf ~/50-System/bin/<name> ~/.local/bin/<name>
# 3. Symlink in ~/bin/ (backup, via ~/.profile — ggf. erst mkdir)
mkdir -p ~/bin
ln -sf ~/50-System/bin/<name> ~/bin/<name>
# 4. Desktop-File Exec= sollte <name> (ohne Pfad) sein
#    → sucht via PATH automatisch in ~/.local/bin/
```

### Desktop-File Exec

Desktop-Files in `~/.local/share/applications/` sollten `Exec=<name>` statt `Exec=/home/bratan/50-System/bin/<name>` verwenden (oder absoluten Pfad zu `~/.local/bin/<name>`). Das funktioniert weil:
- `~/.local/bin/` im PATH liegt → Desktop-Umgebung findet den Wrapper
- Desktop-File bleibt portabel (kopierbar auf anderes System)
- Kein Brechen wenn `50-System/bin/` jemals umzieht

**Pitfall:** Ein Desktop-File mit `Exec=/home/bratan/50-System/bin/<name>` funktioniert zwar, aber `minimax-code --check` scheitert im Terminal weil `~/50-System/bin/` nicht im PATH ist. Immer beide Wege testen.

### PATH-Prüfung

```bash
# Zeigt ob 50-System/bin im PATH ist (sollte NEIN sein!)
echo "$PATH" | tr ':' '\n' | grep '50-System'

# Zeigt ob ~/.local/bin und ~/bin im PATH sind (sollte JA sein!)
echo "$PATH" | tr ':' '\n' | grep -E '\.(local/bin|bin)$'

# Prüft ob ein Wrapper gefunden wird
command -v <name>
```

### Historie dieser Erkenntnis

- **2026-07-03 (MiniMax Hub):** `minimax-hub` Wrapper in `~/50-System/bin/` erstellt, Desktop-File zeigte auf `/home/bratan/bin/minimax-hub`. `~/bin/` existierte nicht. User rief Hub wahrscheinlich nie aus Terminal via `minimax-hub` auf — nur übers Desktop-Menü.
- **2026-07-08 (MiniMax Code):** Gleicher Fehler reproduziert. User testete `minimax-code --check` direkt im Terminal → "command not found". Fix: Symlinks in `~/.local/bin/` und `~/bin/` erstellt. Lesson als Memory + Skill-Dokumentation festgehalten.

### pkill/pgrep-Antipattern: Herstellername matcht Hermes-Subagenten

Wenn ein Wrapper-Prozesse mit `pkill -f "MiniMax"` oder `pgrep -af "MiniMax"` sucht,
matcht das ALLE Prozesse deren cmdline das Wort "MiniMax" enthält — inklusive
Hermes-Subagent-Prozesse die als Modell `MiniMax-M3` verwenden.

**Fix:** pkill/pgrep nur mit exklusiven Patterns, z.B. `.exe`-Suffix:

```bash
# ❌ Falsch — matcht Hermes "MiniMax-M3" + echtes Wine
pgrep -af "MiniMax"

# ✅ Richtig — nur Windows-EXEs + Wine-Infrastruktur
pkill -9 -f "MiniMax Code.exe"
pkill -9 -f "wineserver"
pkill -9 -f "wine-preloader"
# Verifikation mit identischem Pattern:
pgrep -af "(MiniMax Code\\.exe|wineserver|wine-preloader|wine64-preloader)"
```

**Im Python-Template:** Über die Konstante `PROCESS_PATTERN` gesteuert (siehe
`templates/electron-wine-pty-launcher.py` → `kill_prior()`). Bei neuen Wrappern
immer einen app-spezifischen `PROCESS_PATTERN` setzen und den eigenen `pgrep`-
Prozess ausfiltern (der taucht im Match auf wenn er das Pattern selbst in der
cmdline hat).

- [WineHQ: Running Windows Applications](https://wiki.winehq.org/Running_Applications)
- [NSIS Documentation — Silent Install](https://nsis.sourceforge.io/Docs/Chapter4.html#silent)
- [Bottles Documentation](https://docs.usebottles.com/)
- [Electron app.asar format](https://www.electronjs.org/docs/latest/tutorial/asar-archives) — reverse engineering notes
- Sessions: 2026-07-03 MiniMax Hub auf Linux (HailuoAI), GreyHack on Bottles
