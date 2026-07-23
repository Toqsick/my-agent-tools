---

name: linux-system
description: |
  Use when you perform Linux system maintenance and troubleshooting on a Basti-style host — disk usage, package updates, journal logs, broken services, kernel or systemd issues — and need a structured diagnostic + fix flow.
  NOT for non-Linux hosts, GUI desktop troubleshooting, or single-command one-liners that don't need a diagnostic tree.
  Linux host maintenance & troubleshooting toolkit: disk, packages, systemd units, journal analysis, common repair recipes for Ubuntu/Debian/Fedora.
version: 1.13.0
author: Hermes Agent (curator consolidation + MiniMax Hub session 2026-07-03 + Brave-Shields-White-Screen
  pitfall 2026-07-03 + OAuth-Deeplink flow 2026-07-03 + Wine-Registry-Env-Var-Bypass
  2026-07-03 + Manifest-V2-Brave-Side-Effect 2026-07-03 + MiniMax Code PATH-Deployment
  2026-07-08 + pkill-pgrep-Hermes-collision 2026-07-08 + WinBoat-dockur-port-mapping
  + Guest-Server-Architecture + Log-Dir-Struktur 2026-07-08 + systemd-path-drift subsection
  2026-07-13 + Foreground-Watcher reference 2026-07-14)
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - linux
    - maintenance
    - disk
    - cleanup
    - display
    - edid
    - bash
    - audit
    - system
    - wine
    - bottles
    - windows-apps
    - electron
    - asar
    - oauth
    - brave
    - browser
    - ublock-origin
    - sso
    - deeplink
    - xdg-mime
    - url-scheme
    - protocol-handler
    - manifest-v2
    - winboat
    - winapps
    - freerdp
    - windows-vm
    - dockur
    - protonvpn
    - netshield
    - doh
    - dns-block
    - wine-registry
    - in-app-login
    - electron-in-app
    - nextjs-login
    - foreground-watcher
    - background-process
    - monitoring
    - sidecar
    related_skills:
    - security-audit
    - hermes-admin
lane: worker-heavy
reasoning_effort: xhigh
trigger_keywords: ['linux', 'troubleshooting', 'maintenance', 'host', 'disk']
keywords: ['linux', 'troubleshooting', 'maintenance', 'host', 'disk']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['hermes-maintenance', 'linux-system-maintenance']
---



# Linux System — Maintenance & Troubleshooting

Covers: disk cleanup, package/kernel management, display/EDID fixes, bash script auditing, and system inspection.

## Disk Cleanup & System Maintenance

See `references/linux-system-maintenance.md` for full guide.

### Quick Reference
```bash

set -euo pipefail
# Disk usage
df -h / /home
du -sh ~/.hermes/* | sort -rh

# Package audit
apt list --upgradable 2>/dev/null | head -30
dpkg -l | grep -E 'linux-(image|headers|modules)'
dpkg -l | grep '^rc' | wc -l  # orphaned configs

# Kernel cleanup (keep current + one backup)
uname -r  # current kernel

# ⚠️  PITFALL: `apt autoremove` does NOT remove old HWE kernels that
# are still flagged as manually installed. Standard cleanup only
# catches orphans — explicit purge is required for all four packages:
sudo apt purge -y \
  linux-image-<old-version>-generic \
  linux-headers-<old-version>-generic \
  linux-modules-<old-version>-generic \
  linux-modules-extra-<old-version>-generic
# Verify with: dpkg -l | grep -E 'linux-(image|headers|modules)' | wc -l
# (expected: ~8–9 = current kernel packages only)

# rc package purge (in order!)
dpkg -l | grep '^rc' | awk '{print $2}' | xargs sudo dpkg --purge

# Log cleanup
journalctl --disk-usage
sudo journalctl --vacuum-time=7d

# Common caches
du -sh ~/.cache/thumbnails ~/.cache/pip ~/.npm ~/.cache/BraveSoftware
```

### Cleanup Targets
| Target | Path | Root? | Typical Size |
|--------|------|-------|--------------|
| APT cache | `/var/cache/apt/archives/*.deb` | ✅ | <500 MB |
| journalctl | `/var/log/journal/` | ✅ | 200 MB–2 GB |
| Thumbnails | `~/.cache/thumbnails` | ❌ | <1 GB |
| pip cache | `~/.cache/pip` | ❌ | <500 MB |
| npm cache | `~/.npm/_cacache/` | ❌ | <1 GB |
| uv cache | `~/.cache/uv` | ❌ | 2–8 GB |
| huggingface hub | `~/.cache/huggingface/hub/*` | ❌ | 1–10 GB |
| ms-playwright | `~/.cache/ms-playwright` | ❌ | 1–2 GB |
| deja-dup cache | `~/.cache/deja-dup` | ❌ | 1–3 GB |
| Steam shadercache | `steamapps/shadercache` | ❌ | variable |
| Snap revisions | `snap list --all` disabled | ✅ (sudo) | 200 MB–1 GB |
| **Docker build cache** | `docker builder prune -a` | ❌ | **5–20 GB** |
| **Docker unused images** | `docker image prune -a` | ❌ | **5–15 GB** |
| **Docker stopped containers** | `docker container prune -f` | ❌ | <100 MB |
| **Flatpak unused runtimes** | `flatpak uninstall --unused` | ❌ | 2–10 GB |
| **Flatpak app data (USER!)** | `~/.var/app/<id>/` | ❌ | **10–200+ GB** |
| **Ollama models (check dupes)** | `~/.ollama/models` + `/usr/share/ollama/.ollama/models` | ❌ | 5–25 GB each |

### Docker Cleanup (Critical Order)

See `references/docker-flatpak-ollama-cleanup.md` for full guide.

```bash
# ⚠️  ORDER MATTERS: containers → images → build cache
# Stopped containers must be pruned FIRST, otherwise
# docker image prune -a keeps images referenced by them.

docker container prune -f          # Step 1: remove stopped containers
docker image prune -a -f           # Step 2: remove images not used by running containers
docker builder prune -a -f         # Step 3: clear ALL build cache layers
docker volume prune -f             # Step 4 (optional): remove unused volumes
```

**Pitfall:** `docker system prune -a --volumes` does all at once but is aggressive — it removes volumes too. Prefer the sequential approach when you want to preserve volumes.

### Flatpak Cleanup

```bash
# Safe: remove unused runtimes (old GNOME/KDE platform versions, GL drivers)
flatpak uninstall --unused --noninteractive

# ⚠️  INSPECT before nuking: ~/.var/app/ holds real user data
du -h ~/.var/app/ --max-depth=1 | sort -rh | head -10
# Steam games, GNOME Boxes VMs, Bottles prefixes live here — NOT cache!
```

**Pitfall:** Flatpak `--unused` only removes runtimes no app references. Pinned GTK themes (`org.gtk.Gtk3theme.*`) are never removed automatically. Multiple `org.gnome.Platform` versions (1.1 GB each) and GL drivers (4–8 × 450–820 MB) accumulate silently.

### Ollama Duplicate Detection

```bash
# Ollama can store models in TWO locations — check both
du -sh ~/.ollama/models/                          # user-level
du -sh /usr/share/ollama/.ollama/models/          # system-level (ollama user)

# List and remove old models
ollama list
ollama rm <model-name>                            # removes from active OLLAMA_MODELS dir
```

## Display & EDID Fixes

See `references/linux-display-setup.md` for full guide.

### Quick Reference
```bash

set -euo pipefail
# Diagnose
lspci | grep -E "VGA|3D|Display"
xrandr --query
xrandr --verbose | grep -A30 "^<PORT>"

# Custom modeline
cvt 1920 1080 144
xrandr --newmode "1920x1080_cvt144" 452.50 1920 2088 2296 2672 1080 1083 1088 1177 -hsync +vsync
xrandr --addmode DP-1-1 "1920x1080_cvt144"
xrandr --output DP-1-1 --mode "1920x1080_cvt144" --rate 144

# Persistence: create ~/bin/monitor-setup.sh + ~/.config/autostart/monitor-setup.desktop
```

## Bash Script Auditing

See `references/bash-script-audit.md` for full guide.

### Quick Reference
```bash

set -euo pipefail
# Inventory
search_files(path="/home/bratan", pattern="*.sh", target="files")

# Syntax check
bash -n script.sh

# ShellCheck
shellcheck ~/bin/*.sh
```

### Common Bash Bugs
| # | Pattern | Fix |
|---|---------|-----|
| 1 | YAML-sed | Use Python yaml.safe_load/dump |
| 2 | Dead code paths | Remove or add check |
| 3 | `set -e` + side-effect failure | Isolate with `\| true` |
| 4 | `cp` as SQLite backup | Use `sqlite3 .backup` |
| 5 | flock wrong fd pattern | `exec 9>file; flock -n 9` |
| 6 | `$?` with pipefail | Use `${PIPESTATUS[0]}` |
| 7 | `cd` without error check | `cd "$DIR" \|\| { log "ERROR"; exit 1; }` |
| 8 | `((VAR++))` exits 1 when VAR is 0 under `set -e` | Use `set -uo pipefail` (drop `-e`) or `VAR=$((VAR+1))` |
| 9 | `grep -c` returns "N\n" (trailing newline) breaks `[[ "$X" -gt 0 ]]` | `X=$(echo ... \| grep -c ... \| tr -d '\n')` or wrap with `head -1` |
| 10 | `if python3 -c "import sys; sys.exit(0 if $X < -0.05 else 1)"` fails when X is empty | Use `float('${X}')` to guard, or guard with `[[ -n "$X" ]]` first |
| 11 | `PYTHONHASHSEED` randomization breaks `hash()`-based dedup IDs across cron runs | Use `hashlib.md5(content.encode("utf-8")).hexdigest()[:16]` |

## NVIDIA Optimus / Prime on Wayland

See `references/nvidia-prime-wayland-debugging.md` for the full Optimus + Wayland + Flatpak Steam debugging guide.

### Quick Checks
```bash

set -euo pipefail
# Prime env poisoning?
env | grep -E '^(__NV_PRIME_RENDER_OFFLOAD|__GLX_VENDOR_LIBRARY_NAME)='

# prime-run works + routes to NVIDIA?
prime-run glxinfo | grep 'OpenGL renderer'

# Default render should be iGPU (on-demand mode)?
glxinfo | grep 'OpenGL renderer'

# Proton device filter (for Flatpak Steam):
# Steam Launch Options → DXVK_FILTER_DEVICE_NAME="NVIDIA GeForce RTX 5060 Laptop GPU" %command%
```

### Key Pitfalls
1. **Session-global Prime env vars** — `gnome-session-binary` on Zorin/Wayland injects `__NV_PRIME_RENDER_OFFLOAD=1` into ALL processes. Source = oldest PID carrying the vars. Fix: `prime-select on-demand` + reboot.
2. **Flatpak Steam + prime-run** — Host `prime-run` cannot reach `/app/bin/steam` inside sandbox. Use Steam Launch Options with `DXVK_FILTER_DEVICE_NAME` instead.
3. **Empty staging folder** — Game in `steamapps/<title>/` (not `common/`) with 0 bytes = interrupted install. Reinstall via Steam.
4. **`apt purge nvidia-driver-XXX` removes `nvidia-prime`** — `prime-run` disappears. Reinstall `nvidia-driver-XXX-open` to restore.
5. **GRUB Flavour Override (Ubuntu Studio)** — `/etc/default/grub.d/ubuntustudio.cfg` sets `GRUB_FLAVOUR_ORDER=lowlatency` → boots kernel without NVIDIA modules. Fix: `zz-yuno-flavour-generic.cfg` with `GRUB_FLAVOUR_ORDER="generic lowlatency"`. See `references/nvidia-driver-troubleshooting.md` PITFALL 13.

## NVIDIA Driver Troubleshooting

See `references/nvidia-driver-troubleshooting.md` for full guide.

### Quick Checks
```bash

set -euo pipefail
nvidia-smi                    # Driver loaded?
lsmod | grep nvidia           # Kernel modules loaded?
mokutil --sb-state            # Secure Boot blocking modules?
systemctl status nvidia-powerd  # 203/EXEC = corrupted service file
cat /etc/X11/xorg.conf 2>/dev/null  # DANGEROUS if generated by nvidia-xconfig
```

### Key Pitfalls
1. **`nvidia-xconfig` writes `/etc/X11/xorg.conf`** — forces NVIDIA driver, breaks boot if module fails. Use `xorg.conf.d` snippets instead.
2. **`nvidia-powerd.service` 203/EXEC** — service file corrupted (often by Green With Envy). Restore from `/usr/share/doc/nvidia-kernel-common-*/nvidia-powerd.service`.
3. **RTX 50xx (Blackwell) unsupported** — needs `NVreg_OpenRmEnableUnsupportedGpus=1` in `/etc/modprobe.d/nvreg_fix.conf`.
4. **Secure Boot** — Can block unsigned NVIDIA modules, especially with unsupported GPU hacks.
5. **`__NV_PRIME_RENDER_OFFLOAD=1` exported globally** — composites, browsers, innocent viewers all get routed to NVIDIA, games stutter because dGPU is also drawing the desktop AND EC-capped. Check `env | grep __NV_/__GLX_/__GL_` first.
6. **`prime-run` not a shipping binary** — generated by `nvidia-prime` package. Missing? `sudo apt reinstall nvidia-prime` or rebuild wrapper manually.
7. **Vulkan works without `vulkaninfo`** — check `/usr/share/vulkan/icd.d/nvidia_icd.json` + ICD dynamic-load. Do not block diagnosis on missing tools package.
8. **`powerprofilesctl balanced` quietly throttles gaming** — set `performance` before benchmarking.
9. **Boot-Loop Recovery:** If `nvidia-smi` fails after GPU tweaks → check `/etc/X11/xorg.conf` first, remove it, reload modules. See `nvidia-laptop-gaming-tuning/references/boot-loop-recovery.md`.

### "Games used to work, now they don't" — load the readiness script
For Optimus laptops experiencing gaming regressions where the driver is healthy but games still go wrong, run:
```bash

set -euo pipefail
bash /home/bratan/.hermes/skills/devops/linux-system/scripts/nvidia-gaming-readiness.sh
```
Read-only, no sudo, covers driver + GL/Vulkan + Prime env + power/EC + Steam in one pass with red/yellow/green triage.

## System Inspection Workflow
```bash

set -euo pipefail
# 1. Quick health
df -h / /home && free -h && uptime

# 2. Packages & kernels
apt list --upgradable 2>/dev/null | head -30
dpkg -l | grep -E 'linux-(image|headers|modules)'
dpkg -l | grep '^rc'

# 3. Logs & caches
journalctl --disk-usage
du -sh ~/.cache/thumbnails ~/.npm ~/.cache/pip

# 4. Mail client check
dpkg -l | grep -iE "thunderbird|evolution|kmail|geary|claws|mutt"

# 5. NVIDIA GPU check
nvidia-smi 2>/dev/null || echo "NVIDIA driver not loaded"
mokutil --sb-state 2>/dev/null

# 6. Present findings in structured table
```

## SD Card Validation (Fake Detection)

See `references/sd-card-validation.md` for full guide.

### Quick Reference
```bash

set -euo pipefail
# Install f3 (Fight Flash Fraud)
sudo apt install f3

# Identify device
lsblk -f
lsusb | grep -i "reader\|mxt"  # check for known fake readers

# Phase 1: Quick non-destructive roundtrip test (1GB)
sudo mount -o uid=$USER,gid=$USER,umask=000 /dev/sdX1 /mnt
dd if=/dev/urandom of=/tmp/test.bin bs=1M count=1024
cp /tmp/test.bin /mnt/ && sync && cp /mnt/test.bin /tmp/read.bin
cmp /tmp/test.bin /tmp/read.bin && echo "✅ OK" || echo "❌ KORRUPT"

# Phase 2: Full capacity test (destructive, run in background)
sudo umount -l /dev/sdX1
f3write /mnt/          # fills entire card
f3read /mnt/           # verifies all data

# After fake detected → repartition to real capacity
sudo wipefs -a /dev/sdX
sudo parted /dev/sdX --script mklabel msdos
sudo parted /dev/sdX --script mkpart primary fat32 1MiB 100%
sudo mkfs.vfat -F 32 /dev/sdX1
```

**Red flags:** 500GB SD card for <15€, No-Name brand, USB reader `aaaa:8816` (MXTronics), write speed drops to 0 after some point.

## Systemd-User-Unit Path-Drift Detection

**Problem:** Nach Filesystem-Restrukturen (Cluster-Migration, Umzüge) zeigen systemd-User-Units
auf nicht mehr existierende `ExecStart`-Pfade. Der Service ist `disabled` + `inactive`,
aber niemand merkt es, bis ein Tailscale- oder Gateway-Listener auf den toten Port zeigt.

**Bulk-Scan aller User-Units auf tote Pfade:**
```bash
find ~/.config/systemd/user/ -name "*.service" | while read f; do
  cmd=$(grep ^ExecStart "$f" | head -1 | sed 's/ExecStart=//')
  path=$(echo "$cmd" | awk '{print $1}')  # first word (no env prefix)
  echo "$f → $path"
  test -f "$path" && echo "  OK" || echo "  🔴 PATH TOT"
done
```

**Triage bei gefundenen toten Pfaden:**
1. Ist der Service noch relevant? → Unit-Datei korrigieren: `WorkingDirectory` + `ExecStart` auf neuen Pfad setzen
2. Service nicht mehr gebraucht? → `systemctl --user disable <unit>` + Unit-Datei löschen + betroffenen Tailscale-Listener entfernen (`tailscale serve --https=PORT off`)
3. Nach Korrektur: `systemctl --user daemon-reload && systemctl --user start <unit>`

**Siehe auch** `system-security-audit/references/tailscale-dead-listener-triage.md` für die
vollständige Case Study (tokentelemetry.service nach 2026-07-04-Restruktur).

## References

- `references/linux-system-maintenance.md` — Disk cleanup, package/kernel audits, scanner architecture
- `references/docker-flatpak-ollama-cleanup.md` — Docker cleanup order, Flatpak runtime/data distinction, Ollama dual-location model dedup
- `references/linux-display-setup.md` — Display/EDID fixes, xrandr modelines, G-Sync
- `references/bash-script-audit.md` — Bash script auditing, common bugs, safety patterns
- `references/nvidia-prime-wayland-debugging.md` — Optimus + Wayland + Flatpak Steam: Prime env poisoning, Flatpak Steam routing, DXVK device filter, staging detection
- `references/nvidia-driver-troubleshooting.md` — NVIDIA driver pitfalls, xorg.conf boot killer, powerd 203/EXEC, RTX 50xx unsupported, GWE side-effects
- `references/windows-apps-on-linux.md` - Running Windows desktop apps on Linux: installer format ID (NSIS/Inno/InstallShield/MSI), "web first, wine second" strategy, Electron-specific pitfalls (Node.js EBADF, Win11 API gap, NSIS .NET chicken-and-egg, Wine Registry env-var bypass, ProtonVPN NetShield DNS-block vs. Brave-Shields Layers, Manifest V2 toggle side-effects), Bottles vs raw Wine, NVIDIA-GLX-Flatpak-Sandbox-Probleme, Runner-Empfehlung (kron4ek-11.11 für Electron). PLUS: Electron-Render-Diagnose (xwininfo/xwd/wmctrl) und asar-reverse-engineering für OAuth-Token-Workaround.
- `references/browser-cookie-debugging.md` - Chromium-based browser cookie persistence debug: Brave/Chrome empty-cookie-value diagnosis (anti-tracking cleanup), Sync-Status auslesen (Preferences JSON `were_old_google_logins_removed` + `user_selected_sync_types`), Sync-Setup-Workflow mit 24-Wort-Recovery-Code, und X11-Screenshot ohne xdotool via `xwd` + ImageMagick.
- `references/brave-third-party-login-white-screen.md` - Browser-side White-Screen bei OAuth/SSO-Logins: uBlock Origin + uMatrix + Cookie-AutoDelete blocken Resource-Loading tiefer als Brave-Shields. Fix: Inkognito-Modus (Ctrl+Shift+N), dediziertes Profil, oder Filter-Whitelist für `@@||cdn.<app>.com^$important`. PLUS: OAuth-State-Token-Decoding zur Login-Provider-Discovery. **NEU 2026-07-03**: Manifest V2 Toggle (`brave://flags/#brave-extension-manifest-v2`) macht uBlock Origin + uMatrix SCHÄRFER (webRequestBlocking erlaubt) und macht White-Screen-Probleme schlimmer.
- `references/vpn-dns-block-brave-shields.md` - System-DNS-Block vs. Browser-Block unterscheiden. Symptom: White-Screen trotz Inkognito/Shields-aus. Ursache: VPN-Client (ProtonVPN NetShield, AdGuard-VPN, etc.) blockt Tracking-Domains via DNS-Liste (NXDOMAIN). Fix: VPN-Werbeblocker ausschalten ODER Brave DoH auf 'secure' setzen (umgeht systemd-resolved via Cloudflare). PLUS: Diagnose-Matrix (`nslookup` system vs 1.1.1.1, Inkognito-Test).
- `references/electron-in-app-login-discovery.md` — In-App-Login-Pattern mit built-in Next.js-Login-Seite im Electron-Renderer (alternative zu externem OAuth-Deeplink). Window-Type-Diagnose, minimax-agent-config.json Token-Injection, Login-API-Endpoints (phone/sms/github/etc.), Onboarding-Skip-Diagnostik.
- `references/electron-oauth-deeplink-linux.md` - Vollständiger OAuth-Login-Flow für Electron-Apps unter Wine/Bottles: xdg-mime + .desktop-File für URL-Schema-Handler (`<app>://auth-callback`), Reverse-Engineering des Deeplink-Formats aus `app.asar` und Browser-UI, manuelle Trigger-Befehle (`wine app.exe <scheme>://...`), Drei-Schichten-Token-Modell (Browser-Cookies → Bridge-Cookies → Electron-Storage). PLUS: Diagnose-Matrix Wine vs Browser vs DNS-Block für "Login klappt nicht". **NEU 2026-07-03**: Wine-Registry-Env-Var-Bypass via `wine reg add HKCU\\Environment /v HILO_USER_TOKEN /d <token>` als Workaround wenn Shell-Env-Durchreichung nicht funktioniert.
- `references/windows-vm-seamless-apps.md` — Docker-basierte Windows-VM mit nahtlosem RemoteApp-Integration (WinBoat/WinApps + dockur/windows + FreeRDP 3.x). Entscheidungsbaum VM vs Wine/Bottles, Setup-Schritte, FreeRDP 3.x Installation und Symlink-Pitfall, Architektur-Diagramm, ESU-Info. Parallele Alternative zu `references/windows-apps-on-linux.md`.
- `references/foreground-watcher-pattern.md` — **NEU 2026-07-14.** Bauanleitung für durable Background-Monitoring-Prozesse unter Hermes. Nutzt Foreground-Loop + STOP-Marker statt nohup/disown (die unter Hermes reaped werden). Mit Implementation-Template, Deployment-Pattern und Pitfall-Table. Angewendet in `grok-monitor`.
## Scripts & Templates

- `scripts/cleanup-workflow.sh` — Reusable end-to-end cleanup recipe (pre-flight → kernels → rc → journalctl → user caches → verify)
- `scripts/nvidia-gaming-readiness.sh` — Optimus + NVIDIA gaming readiness probe (driver / GL / Vulkan / Prime-env / power / Steam) — use when "games used to work, now they don't"
- `templates/electron-wine-pty-launcher.py` — Python PTY-Wrapper-Starter für moderne Electron-Apps (umgeht Node.js createWritableStdioStream-EBADF-Crash in Bottles+Wine). Mit `--check`/`--kill`/`--log` Flags und Token-Datei-Support für OAuth-Login-Workaround. **NEU 2026-07-08:** `kill_prior()` mit präzisem `PROCESS_PATTERN`-Regex (vermeidet false-positives durch Hermes-Subagent-Modellnamen), `wineserver` + `wine-preloader`/`wine64-preloader` explizite kill-Targets und Verifikations-Schritt mit identischem Pattern. PATH-Hinweis: primär nach `~/.local/bin/` deployen (im PATH), Backup nach `~/bin/`. Pfade oben anpassen, nach `~/.local/bin/` kopieren. Reuse für jede Electron-App in Bottles. Siehe `references/windows-apps-on-linux.md → Wrapper Deployment PATH Setup`.
- `templates/wine-registry-envvar-inject.py` — Wine-Registry-Env-Var-Injector (`wine reg add HKCU\Environment /v NAME /d VALUE`). Alternative wenn Shell-Env nicht durchgereicht wird. Siehe `references/windows-apps-on-linux.md` Pitfall-Section.

### Self-service Fix-Scripts (Pattern)

When a fix needs multiple sudo/inspect steps, write a **self-service script** in `/home/bratan/fix-scripts/<task>.sh` that Basti runs himself. Use `templates/self-service-fix.sh` as the starting point — provides:

- `--dry-run` for pre-flight review (echo-only, no changes)
- `--askpass` for piped sudo password (when not in a TTY)
- Structured logfile in `/tmp/<scriptname>.log`
- Color-coded output: `▸` step, `✔` ok, `⚠` warn, `✖` fatal
- `need_sudo()` helper that figures out the right sudo invocation
- Diagnose-Snapshot as Step 1 (rule: never repair blind)

**Basti's Preference — "Langfristig sinnvoll machen":** Basti bevorzugt durable, PATH-symlinked Tools
in `~/50-System/bin/` + `~/bin/`-Symlinks über einmalige Fix-Skripte. Wenn ein Workaround
oder eine Überwachungslösung mehr als 1× gebraucht wird, direkt als wiederverwendbares Tool
mit `--check`/`--dry-run`/`--help` Flags bauen, nicht als Wegwerf-Skript. Die `grok-*`-Tools
(grok-preflight, grok-monitor, grok-audit) sind das Referenz-Design: drei Bash-Skripte,
PATH-symlinked, mit klarem Lifecycle (start/stop/status).

Workflow:
```bash

set -euo pipefail
cp ~/.hermes/skills/devops/linux-system/templates/self-service-fix.sh \
   /home/bratan/fix-scripts/<task>.sh
# Edit: replace STEP 2..N with actual repair steps
bash /home/bratan/fix-scripts/<task>.sh --dry-run    # preview
bash /home/bratan/fix-scripts/<task>.sh              # apply (asks pw if needed)
systemctl reboot                                     # when next-step says so
```

### Windows Desktop Apps auf Linux (Wine / Bottles / Web-Alternative)

See `references/windows-apps-on-linux.md` for full guide.

**Entscheidungsbaum:**
```
Windows Desktop App gewünscht?
├─ Gibt es eine Web-Version/API?
│  └─ ✅ Web first testen (0 Setup)
├─ Datei-Signatur prüfen: `file setup.exe`
│  ├─ "Nullsoft Installer" (NSIS) → `7z x setup.exe -o./extracted`
│  │  └─ ⚠️ Silent `/S` hängt bei Electron-Installer → 7z zwingend
│  │  └─ Bundle liegt als `.7z` oder Verzeichnis in `$PLUGINSDIR`
│  ├─ "Inno Setup" → `innoextract setup.exe -d ./extracted`
│  ├─ "InstallShield" → `unrar x` / `cabextract`
│  └─ MSI → `msiextract` (msitools)
├─ Electron-App? → Besondere Fallstricke:
│  • Auto-Update / OAuth- / FileSystem-Zugriff oft kaputt
│  • Web-Alternative fast immer besser
│  • EBADF ohne PTY-Wrapper → `templates/electron-wine-pty-launcher.py`
│  • Heartbeat-Zählen als GUI-Health-Proxy (Wayland überlebt)
├─ Sibling-App vom selben Hersteller? → Bottle-Recycling:
│  • Gleiches Wine-Prefix + Runner spart 4-5 GB Disk
│  • Bundle direkt nach drive_c/ kopieren statt neuer Bottle
│  • Siehe `references/windows-apps-on-linux.md` → Sibling-App Bottle Recycling
└─ Bottles statt raw Wine bei komplexen Installern
   → `flatpak install flathub com.usebottles.Bottles`
   → Wrapper nach `~/.local/bin/` deployen (nicht `~/50-System/bin/`)
   → PATH-Prüfung: `command -v <name>` nach Deployment

**Pitfall:** Bottles-Backups enthalten NUR Konfiguration + System-DLLs — die
   installierte App muss separat existieren. Backup-Tarball allein reicht NICHT.

### Bottles Flatpak auf NVIDIA-Systemen

**Bekannte Probleme:**
- Bottles-Journal zeigt `Unable to load libGLX_nvidia.so.0` bei NVIDIA-GPUs → NVIDIA-Treiber-Libs sind im Flatpak-Sandbox nicht sichtbar. Fix: `flatpak override --user --env=FLATPAK_GL_DRIVER=nvidia com.usebottles.bottles`
- Bottles 64+ hat die `use_system_runtime`-Option entfernt — kein einfacher "Host-Wine"-Modus mehr
- `bottles-cli` kann NICHT von außerhalb des Flatpak-Sandbox aufgerufen werden (benötigt Python 3.13 + pycurl im Flatpak-Kontext)

**Runner-Empfehlung für NVIDIA-Systemen (Electron-Apps):**
- **`kron4ek-wine-11.11-amd64` (Wine 11.11) ist erste Wahl für Electron-Apps** auf NVIDIA-Systemen
- `wine-ge-proton` (Wine 8) crasht moderne Electron-Apps bei `KERNEL32.GetProcessInformation` (Win11-API fehlt) — NICHT für Electron verwenden!
- `soda`-Runner (Wine 9.0): zu alt
- `caffe`-Runner (TkG 9.7): hat dieselbe Lücke wie GE-Proton
- **Node.js Stdio EBADF** (Electron-Eigenheit): Electron-Apps starten nicht via Pipe-Redirect, brauchen PTY — siehe `references/windows-apps-on-linux.md` Killer-Pitfall #1

**Diagnose:**
```bash
# Bottles-Journal auf GLX-Fehler prüfen
cat ~/.var/app/com.usebottles.bottles/data/bottles/journal.yml | grep "GLX\|libGLX\|NVIDIA"
# Verfügbare Runner anzeigen
ls ~/.var/app/com.usebottles.bottles/data/bottles/runners/
```

**Runner-Wechsel:** Bottles GUI → Bottle auswählen → Einstellungen → Runner → `kron4ek-wine-11.11-amd64` auswählen.

**Pitfall:** `bottles-cli` startet von außen mit `ModuleNotFoundError: No module named 'bottles'` oder `No module named 'pycurl'` — die CLI erwartet Python 3.13 + Flatpak-interne Libs. Immer über `flatpak run --command=bottles-cli com.usebottles.bottles <args>` oder die GUI arbeiten.

### Windows VM Seamless App Integration (VM-Ansatz, Alternative zu Wine/Bottles)

Paralleler Ansatz zu Wine/Bottles: **echte Windows-VM in Docker mit RDP RemoteApp-Protokoll**.
Apps erscheinen als native Linux-Fenster, nicht als VM-Desktop.

See `references/windows-vm-seamless-apps.md` for full guide.

**Wann VM statt Wine:**
| Kriterium | Wine/Bottles | VM (WinBoat/WinApps) |
|-----------|-------------|---------------------|
| Große Suiten (Adobe, Office) | ⚠️ Fragil | ✅ Echt-Windows-Kompatibilität |
| Security-kritische Apps | ❌ Unsicher | ✅ Echte Isolation |
| Kernel-Treiber / Anti-Cheat | ❌ Unmöglich | ✅ Win-VM = native Umgebung |
| Einfache EXE einmalig | ✅ Schnellster Weg | ❌ 30 min Setup |
| Disk-Bedarf | ~2-5 GB | ~30-64 GB (Win-Image) |
| GPU/DirectX | ✅ (DXVK/VKD3D) | ⚠️ Nur mit GPU-Passthrough |

**Empfohlen: WinBoat** (github.com/TibixDev/winboat, 21.9k ⭐)
- AppImage laden → GUI-Klick → Docker-Container mit dockur/windows
- FreeRDP 3.x RemoteApp-Protokoll für nahtlose Fenster
- Automatische Windows-Installation (~30 min)
- App-Icons erscheinen im Linux-Startmenü

**Technische Voraussetzung: FreeRDP 3.x (NICHT 2.x!)**
```bash
# ⚠️ PITFALL: freerdp2-x11 = v2.11.5 (zu alt!). freerdp3-x11 = v3.5.1 (richtig)
sudo apt install -y freerdp3-x11
sudo ln -sf /usr/bin/xfreerdp3 /usr/local/bin/xfreerdp  # Binary heißt xfreerdp3
# Sound checken: ldd /usr/bin/xfreerdp3 | grep -E 'pulse|alsa|opus'
```

**Alternativ: WinApps** (github.com/winapps-org/winapps, 15.5k ⭐)
- Manuelleres Setup, mehr Kontrolle
- Apps einzeln als RDP-RemoteApp registrieren

**Pitfall:** WinBoat Electron zeigt beim Start `NSS error code: -8018` — cosmetic.
Wayland + cua-driver = WinBoat-Fenster nicht direkt capturebar (User muss klicken).
Win10 EOL 14.10.2025, Consumer-ESU kostenlos bis 12.10.2027 mit MS-Account-Sync.

### Electron Login: Zwei Patterns — Externes OAuth vs. In-App-Login

Electron-Apps haben zwei grundlegend verschiedene Login-Mechanismen:

**Pattern A — Externes OAuth (siehe `references/electron-oauth-deeplink-linux.md`):**
App öffnet Browser mit Login-URL → OAuth-Provider → Deeplink-Callback zurück zur App.
Braucht xdg-mime + .desktop-Handler + Wine-Durchschleifung.
Beispiel: MiniMax Hub via `account.minimax.io/unified-login`.

**Pattern B — In-App-Login (siehe `references/electron-in-app-login-discovery.md`):**
Login-Formular ist als Next.js/React-Seite im `app.asar` gebündelt und wird direkt
im Electron-Renderer angezeigt — **kein externer Browser nötig**.
Erkennbar an Logs: `navigateToLogin → Registered window: type=login`.
Login über API-Endpoints: `matrix/api/v1/user/login/phone`, `sms/send`.
Token sitzt in `minimax-agent-config.json` unter `tokens.accessToken`.
Beispiel: MiniMax Code 3.0.47 via `agent.minimax.io`.

**Diagnose vom Session-Start:** Log-Zeilen verraten sofort welches Pattern.
`[Auth] navigateToLogin triggered` = In-App. `[Auth] Opening browser: ...` = Extern.

### Electron-OAuth-Login via xdg-mime URL-Scheme-Handler (Pattern A)

Für Apps die OAuth/SSO machen und per `app<scheme>://auth-callback?token=...` Deeplink
in die Wine-App zurückfließen lassen.

Siehe `references/electron-oauth-deeplink-linux.md` für:
- URL-Scheme aus `app.asar` extrahieren (strings + `setAsDefaultProtocolClient`)
- `.desktop`-File mit `MimeType=x-scheme-handler/<scheme>;` + `%u`-URL-Platzhalter
- `xdg-mime default <file>.desktop x-scheme-handler/<scheme>` Registrierung
- Manuelles Triggern: `wine app.exe '<scheme>://auth-callback?accessToken=XYZ'`
- **Wine-Registry-Env-Var-Bypass:** wenn Shell-Vars nicht durch Wine durchgereicht werden, schreibe in `HKCU\Environment /v HILO_USER_TOKEN /d <token>`
- Drei-Schichten-Token-Modell (Browser-Cookies → Bridge-Cookies → Electron-Storage)
- Diagnose-Matrix für "Login klappt nicht" (Wine vs Browser vs DNS-Block)

**Pitfall:** Wenn `%u` im Exec fehlt, kommt die URL nicht beim Wine-Prozess an.
Bei `app.on('second-instance', ...)` liest die App `argv[argv.length-1]`, dann ist
das URL der letzte CLI-Argument.

**⚠️ Wine-Env-Var-Workaround:** Wenn `HILO_USER_TOKEN`-Shell-Env nicht durch Wine durchgereicht wird (testbar via `wine cmd /c 'echo %HILO_USER_TOKEN%'` zeigt literal `%HILO_USER_TOKEN%` leer), dann:
```bash
WINEPREFIX=/path/to/bottle wine reg add 'HKEY_CURRENT_USER\Environment' \
  /v HILO_USER_TOKEN /t REG_SZ /d '<JWT-TOKEN>' /f
```
Die Wine-Registry setzt Env-Vars für jeden Child-Prozess persistent. Funktioniert zuverlässig für Token-Vars, OAuth-Tokens und persistente Konfiguration.

### Brave-Browser White-Screen-Diagnose (OAuth-Login-Falle)

Bei OAuth-Login-White-Screen in Brave in **drei Schichten** prüfen:

1. **Schicht 1 (Inkognito testen):** uBlock Origin + uMatrix + Cookie-AutoDelete. Fix: Inkognito-Modus (extensions standardmäßig aus)
2. **Schicht 2 (Shields ausschalten):** Brave Shields für Domain ausschalten
3. **Schicht 3 (VPN-DNS-Block prüfen):** System-DNS via VPN-Werbeblocker (ProtonVPN NetShield etc.). Fix: VPN-Werbeblocker aus ODER Brave DoH auf 'secure' setzen

Siehe `references/brave-third-party-login-white-screen.md`, `references/vpn-dns-block-brave-shields.md` und `references/electron-oauth-deeplink-linux.md` für Details.

**Manifest V2 Toggle (NEU 2026-07-03):**
- `brave://flags/#brave-extension-manifest-v2` aktivieren erlaubt uBlock Origin/uMatrix/Cookie-AutoDelete das volle `webRequestBlocking`-API zu nutzen
- Aber: Macht die drei Schichten White-Screen-Verstärker — Electron-Login-Apps haben weniger Chancen durchzukommen
- Symptom: Im normalen Tab White-Screen, im Inkognito manchmal auch wenn Filter-Extensions standardmäßig aus sind
- Gegen-Symptom: Wenn du **vorher** ohne Probleme loggen konntest und nach MV2-Toggle plötzlich White-Screen: erst MV2 wieder ausschalten bevor Inkognito testen
