# CLAUDE.md Host Context (Migrated 2026-07-07)

Dieser Content ist der einzigartige Teil aus ~/CLAUDE.md, der in ~/AGENTS.md
nicht enthalten ist. CLAUDE.md ist die detailliertere Maschinen-Beschreibung.

## Vollständige Directory-Map (mit Inhalt)

| Cluster | Contents |
|---|---|
| `00-Meta/` | Meta-index: `navigation.md` (canonical map), `README.md`, `DESCRIPTION.md`, model-handoff briefings |
| `10-Projekte/10-active/` | Active dev: `greyhack-tools/`, `odysseus/`, `linux-assistant/`, `github-mcp-server/`, `tokentelemetry/`, `yuno-cleaner/`, `yuno-dashboard/`, `yuno-ui/`, `yuno-voice-bot/`, `cp77-modding/`; plus `projects/` — canonical executable sources for `sysdoctor`, `greysync`, `gmail-organizer` (the `50-System/bin` symlink targets) — and small scratch dirs (`build/`, `dev-workspace/`, `workspace/`, `playwright-tests/`) |
| `10-Projekte/20-experimental/`, `30-staging/`, `40-archive/` | WIP / staged / retired projects |
| `20-Workspace/` | Daily driver: `scripts/` (cron jobs), `fix-scripts/` (NVIDIA/gaming perf fixes), `logs/`, `results/`, `tmp/` |
| `30-Library/` | Read-only: eBooks, forked GreyHack community repos, `steam_backup_toolkit/`, `LenovoLegionLinux/` (kernel module + fan control — **not applicable to this MEDION chassis**, present but unused) |
| `50-System/` | `bin/` (custom scripts — must stay in `$PATH`), `backups/`, `export/` (systemd units, DB dumps) |

## Symlink-Fix Stand (2026-07-05)

`~/50-System/bin/` symlinks (`sysdoctor`, `greysync`, `gmail-organizer`) wurden post-restructure
gefixt → zeigen auf `10-Projekte/10-active/projects/<name>/<name>.py`.
Die copies in `greyhack-tools/tools/` und `30-Library/greyscripts/tools/` sind non-executable
CI-mirror/build copies, NICHT der Tool-Source.

`~/.steampath` ist ein dangling symlink (`~/.steam/sdk32/steam`), wahrscheinlich weil `/mnt/DATA`
nicht gemountet ist — left untouched.

## Host-Facts (detailliert)

- OS: Zorin OS 18.1 (Ubuntu 24.04 Noble), GNOME 46, kernel `6.17.0-35-generic` (HWE).
- Session: **Wayland** (`zorin-wayland`). X11 (`zorin-xorg`) available at GDM für NVIDIA Coolbits.
- Chassis: **MEDION ERAZER** (NOT Lenovo Legion despite `30-Library/LenovoLegionLinux/` existing).
- CPU: Intel i7-13620H (10c/16t).
- GPU: NVIDIA RTX 5060 Laptop 8GB GDDR7 (PRIME=nvidia, `nvidia-powerd` Dynamic Boost).
  Power limit: **default 80W, min 5W, max 115W** (software-adjustable via `nvidia-smi -pl`).
- RAM: 15GB + 7.7GB zram swap (`vm.swappiness=120` seit Optimax Stufe-5).
- Root FS: single NVMe partition (`/dev/nvme0n1p3`), 65-75% full.
- Shell: **bash** (`$SHELL=/bin/bash`). fish is NOT installed despite older notes.

## Security Baseline

UFW active (default deny incoming), no SSH server installed, no empty passwords,
no NOPASSWD sudo, Secure Boot + TPM2 + kernel lockdown active.
Expected listeners: `127.0.0.1:8333` (Hermes API), `127.0.0.1:631` (cupsd), `*:3000` (gitea, UFW-blocked).

## Claude Code Plans (Archiviert)

3 Implementation-Pläne aus Claude Code Sessions:
- `functional-snacking-waffle.md` (8.3KB)
- `hey-kannst-du-in-generic-gray.md` (17.2KB)
- `streamed-twirling-rossum.md` (6.1KB)

Diese liegen unter `references/` und sind Claude-Code-spezifische Plan-Dokumente.
