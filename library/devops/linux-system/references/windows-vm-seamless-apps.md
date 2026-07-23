# Windows VM Seamless App Integration — WinBoat & WinApps

Gegenstück zum Wine/Bottles-Kompatibilitäts-Ansatz (`references/windows-apps-on-linux.md`).
Hier: **echte Windows-VM im Docker-Container mit RDP RemoteApp-Protokoll** — Apps erscheinen
als native Linux-Fenster, nicht als VM-Desktop.

## Architektur (WinBoat)

```
Linux Desktop (Wayland/X11)
  ┌─────────────────────┐
  │ WinBoat Electron    │  ← GUI für Setup + Verwaltung
  └─────────┬───────────┘
            │ xfreerdp3 → RDP (RemoteApp Protocol)
            ▼
  ┌─────────────────────┐
  │ Native Linux-Fenster│  ← Jede Win-App als eigenes Fenster
  │ mit Windows-Inhalt  │    (nahtlos, kein VM-Rahmen sichtbar)
  └─────────────────────┘
            ▲
  docker run (dockur/windows)  ← Docker-Container managt KVM/QEMU
            │
  ┌─────────────────────┐
  │ Win10/11 VM         │  ← Headless, nur RDP-Dienst aktiv
  │ (KVM im Container)  │
  └─────────────────────┘
```

## Entscheidungsbaum: VM (diese Datei) vs. Wine/Bottles

```
Windows-App gewünscht?
├─ Einfaches Tool / kleine App (< 500 MB)?
│  └─ Wine/Bottles zuerst testen (schneller, kein 117 GB Disk)
├─ Komplexe App (Adobe, Office, große Suite)?
│  └─ WinBoat/VM-Ansatz (echte Windows-Kompatibilität)
├─ Braucht GPU/DirectX für Gaming?
│  └─ VM mit GPU-Passthrough ODER Wine/Proton (Spielabhängig)
├─ Sicherheitskritisch (Banking, Behördensoftware)?
│  └─ VM-Ansatz (echte Windows-Isolation, eigener Netzwerkstack)
└─ Einmalig EXE ausführen?
   └─ Wine testen, wenn das crasht → VM
```

## Vergleich der VM-Lösungen

| Tool | ⭐ Stars | Setup | Nahtlose Fenster | Docker | Windows Management |
|------|---------|-------|------------------|--------|-------------------|
| **WinBoat** | 21.9k | Einfach (AppImage + Klick-GUI) | ✅ RemoteApp via FreeRDP 3.x | ✅ dockur/windows Automatisch | Automatisch via GUI |
| **WinApps** | 15.5k | Manuell (VM + RDP + Wrapper pro App) | ✅ RemoteApp via FreeRDP 3.x | ✅ Eigenes Docker-Compose | Manuell (Apps im RDP-Session-Manager registrieren) |
| **GNOME Boxes** | — | Einfach (GUI-Klick) | ❌ Full-Desktop-VM-Fenster | ❌ Native KVM | Manuell (in der VM) |
| **Virt-Manager** | — | Medium | ❌ Full-Desktop-VM-Fenster | ❌ Native KVM | Manuell |

## FreeRDP 3.x Setup (Voraussetzung)

### Installation auf Ubuntu 24.04

```bash
# ⚠️ PITFALL: NICHT freerdp2-x11 installieren (v2.11.5, zu alt für WinBoat!)
sudo apt install -y freerdp3-x11  # v3.5.1 in noble-updates

# Binary heißt xfreerdp3, WinBoat/WinApps erwarten 'xfreerdp'
sudo ln -sf /usr/bin/xfreerdp3 /usr/local/bin/xfreerdp

# Sound-Support verifizieren:
ldd /usr/bin/xfreerdp3 | grep -E 'pulse|alsa|opus'
# Muss liefern: libpulse.so.0, libopus.so.0, libpulsecommon...
```

### Version prüfen
```bash
xfreerdp --version          # "This is FreeRDP version 3.5.1 (n/a)"
apt-cache policy freerdp3-x11  # Zeigt Source: noble-updates
```

## WinBoat Setup

### 1. AppImage holen (141 MB)
```bash
mkdir -p ~/bin/winboat && cd ~/bin/winboat
wget https://github.com/TibixDev/winboat/releases/download/v0.9.0/winboat-0.9.0-x86_64.AppImage -O winboat.appimage
chmod +x winboat.appimage
```

### 2. Starten
```bash
cd ~/bin/winboat
./winboat.appimage
```

### 3. In der GUI
- "Install Windows" klicken
- Specs: 4 GB RAM, 4 vCPUs, 64 GB Disk, Win10 Pro
- ~30 min warten (Windows-Installation im Docker-Container)

## WinApps Setup (Alternative zu WinBoat)

```bash
# Repository klonen
git clone https://github.com/winapps-org/winapps.git ~/bin/winapps
cd ~/bin/winapps

# Docker-Image bauen (dockur/windows als Basis)
docker compose build

# RDP-Konfiguration: FreeRDP 3.x Binary-Pfad prüfen
# WinApps sucht nach xfreerdp — unser Symlink in /usr/local/bin/xfreerdp sollte reichen

# Konfiguration: apps/winapps.yml editieren
# Windows-Apps manuell pro Eintrag registrieren
```

## Pitfalls

| Problem | Ursache | Fix |
|---------|---------|-----|
| `NSS error code: -8018` beim WinBoat-Start | Electron NSS-Zertifikats-Lookup, **cosmetic** | Ignorieren, läuft trotzdem |
| `xfreerdp: command not found` | Binary heißt `xfreerdp3`, nicht `xfreerdp` | `sudo ln -sf /usr/bin/xfreerdp3 /usr/local/bin/xfreerdp` |
| FreeRDP 2.x (v2.11.5) statt 3.x installiert | Falsches apt-Paket | `sudo apt remove freerdp2-x11 && sudo apt install freerdp3-x11` |
| Kein Sound in Windows-Apps | FreeRDP ohne PulseAudio/Opus gebaut | `ldd /usr/bin/xfreerdp3 | grep pulse` — wenn leer: `sudo apt install --reinstall freerdp3-x11` |
| Wayland: WinBoat-Fenster nicht im cua-driver-Capture | Wayland-Compositor-Sicherheit, Fenster ist auf einem anderen Virtual Desktop | User muss manuell klicken (wmctrl bestätigt das Fenster) |
| VM bei 100% CPU dauerhaft | GPU fehlt, CPU muss Software-Rendering + VM | RAM von 4 GB auf 3 GB reduzieren; GPU-Passthrough für Gaming |
| Host-RAM knapp (15 GB systemweit) | 4 GB für VM + ~9 GB Host = 13 GB, wenig Puffer | VM-RAM auf 2-3 GB reduzieren; zram hilft bei Swapping |
| Win10-EOL (14.10.2025) | Microsoft stellt Updates ein | Consumer-ESU kostenlos bis 12.10.2027 mit MS-Account-Sync |
| Disk voll (500 GB root, 460 GB belegt) | VM braucht ~48-64 GB extra | yuno-cleaner vor Setup laufen lassen |
| **Language falsch gewählt (English statt Deutsch)** | LANGUAGE=English in docker-compose.yml — kann nicht nachträglich gewechselt werden | Neuer Container + Install von vorne, ODER Win10-Sprachpaket nachinstallieren (Settings → Language) |
| WinBoat restartet Container nach erstem Install | WinBoat ersetzt docker-compose.yml, stoppt Container, startet neu mit geänderten Ports | Kurze "Guest API offline"-Phase (1-2 min) ist normal. Winboat-Log zeigt "Going to replace compose config" → "Started" |
| Guest-Server bleibt offline (>5 min nach Install) | QEMU-KVM im Container bootet Win10 nicht | `docker logs WinBoat --tail 50` checken; evtl RAM_SIZE zu niedrig (4 GB Minimum für Win10) |

## WinBoat Internals & Troubleshooting

### Port Mapping Schema (dynamisch)

WinBoat verwendet **10er-Port-Ranges pro Service**, nicht Single-Ports. Docker-Compose wird von WinBoat generiert — die Ports ändern sich nach einem Config-Replace:

| Dienst | Container-Port | Host-Port-Range | Beispiel |
|--------|---------------|-----------------|----------|
| RDP (TCP) | 3389 | 47300-47309 | `127.0.0.1:47300->3389/tcp` |
| RDP (UDP) | 3389 | 47310-47319 | `127.0.0.1:47310->3389/udp` |
| Guest API (QMP) | 7148 | 47280-47289 | `127.0.0.1:47280->7148/tcp` |
| QEMU Monitor | 7149 | 47290-47299 | `127.0.0.1:47290->7149/tcp` |
| VNC/Debug | 8006 | 47270-47279 | `127.0.0.1:47270->8006/tcp` |

**Pitfall:** Die tatsächlichen Host-Ports sind nicht vorhersagbar — sie hängen vom installierten Docker-Netzwerk und vorherigen Port-Belegungen ab. Immer per `docker ps --filter "name=WinBoat"` die aktuellen Mappings abfragen.

### WinBoat Guest Server Architecture

WinBoat installiert im Windows-Gast einen **Go-basierten Guest Server** via `nssm.exe` (Windows Service Manager):

```
~/.winboat/oem/
├── winboat_guest_server.exe   # Go binary, 2-stufig: install.bat deployt + nssm registriert
├── winboat_guest_server.zip   # Fallback zum manuellen Entpacken
├── install.bat               # Wird beim ersten VM-Start ausgeführt (OEM-Skript)
├── RDPApps.reg               # Registry-Key für RemoteApp-Registrierung
├── auth.hash                 # Authentifizierungs-Hash für Guest API
├── nssm.exe                  # Windows Service Manager (startet Go-Server als Service)
├── main.go / argon2.go / securekey.go / util.go  # Go-Quellcode
└── scripts/                  # Hilfsskripte
```

**Health-Check-Flow:**
1. WinBoat pollt `http://127.0.0.1:<guest-api-port>/health` im 3s-Intervall
2. Während Win10 installiert wird → `FetchError: read ECONNRESET` (logisch, Win10 läuft noch nicht)
3. Nach Windows-Setup → `WinBoat Guest Server is up and healthy!` → State wechselt zu "Completed"
4. Danach: WinBoat tauscht docker-compose.yml (Config-Replace) → Neustart → State again "Running"

### Log-Dateien (für Debugging)

```
~/.winboat/
├── install.log      ❗ **Primäre Fehlerquelle** — Win10-Install-Verlauf + Guest-API-Polling-Log
├── container.log    Docker-Layer-Pull (nur beim ersten Start), Container-Start-Events
├── winboat.log      WinBoat-Electron-interne State-Machine (Config-Replace, Transitions)
├── docker-compose.yml  Von WinBoat generiert — NICHT manuell editieren (wird überschrieben)
└── winboat.config.json  WinBoat-GUI-Einstellungen (scale, device-passthrough, customApps)
```

### Aktuelle Windows-Install-Timing (Basti's Setup, 2026-07-08)

| Zeit | Phase | Dauer |
|------|-------|-------|
| 21:11:45 | Container erstellt + Image pulled (93 MB QEMU-Pakete, ~20 MB Layer) | — |
| 21:18:56 | Erste Guest-API-Health-Checks (Win10-Installer läuft) | ~7 min |
| 21:23:31 | **Installation completed successfully** | **~12 min** |
| 21:24:56 | Container-State "Running" | ~1 min |
| 21:25:44 | WinBoat Config-Replace (neue Ports, USB-Devices) | ~1 min |
| 21:25:52 | Guest Server "online, passing through devices" | ~8 sec |

**Pitfall:** Während des Config-Replace schreibt WinBoat eine neue docker-compose.yml und restartet den Container. `docker ps` zeigt "Up X minutes" durchgehend wegen Änderungen am Container-Namen — der Credential/Port-Reset ist trotzdem passiert.

## Wichtige ESU-Information (Windows 10 EOL)

Windows 10 **end of life** ist der 14. Oktober 2025. ABER:
- **Consumer-ESU** (Extended Security Updates) ist **kostenlos** für Privatnutzer bis **12. Oktober 2027**
- Voraussetzung: Microsoft-Konto mit dem Win10-Gerät synchronisieren
- Keine neuen Features — nur Sicherheitspatches
- Danach: Upgrade auf Win11 im gleichen Container nötig (250 GB Disk empfohlen)

## Verifikation (ob alles läuft)

```bash
# WinBoat-Prozess prüfen
wmctrl -l | grep -i winboat
# → 0x...  0 bratan-17-P1 WinBoat

# FreeRDP 3.x
xfreerdp --version
# → "This is FreeRDP version 3.5.1 (n/a)"

# Docker
docker ps | grep windows
# → container-name  dockur/windows  Up X minutes

# FreeRDP Sound
ldd /usr/bin/xfreerdp3 | grep -E 'pulse|alsa|opus'
```

## Quellen / Deep Research

- WinBoat: https://github.com/TibixDev/winboat (21.9k ⭐, MIT)
- WinApps: https://github.com/winapps-org/winapps (15.5k ⭐, MIT)
- dockur/windows: https://github.com/dockur/windows (Docker-Image, KVM in Container)
- FreeRDP 3.x Release Notes: https://www.freerdp.com/2024/09/29/3-5-0/
- Win10 ESU: https://www.bleepingcomputer.com/news/microsoft/microsoft-quietly-extends-free-windows-10-esu-support-to-october-2027/