---

name: security-audit
description: |
  Use when you run a Linux security audit on a Basti/Zorin workstation — fwupd HSI score, TPM state, Secure Boot, SSH config, kernel lockdown, sudoers, fail2ban, exposed daemons — and need a baseline + findings report.
  NOT for live penetration testing, red-team operations (use security/red-team skills), or non-Linux/macOS hosts.
  Structured Linux security audit: TPM/Secure Boot/HSI baseline, SSH/sudoers/kernel lockdown checks, fail2ban/UFW status, finding classification + recommendations.
version: 1.0.0
author: Hermes Agent (curator consolidation)
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - linux
    - security
    - fwupd
    - hsi
    - tpm
    - secure-boot
    - audit
    - ollama
    - permissions
    related_skills:
    - linux-system-maintenance
    - hermes-admin
lane: worker-heavy
reasoning_effort: xhigh
agent: Verifier
routing_hint: '**Agent-Scope:** Adversarial QA, audits, security scans, gates. Off-scope:
  building, designing, writing — return to Yuno for re-route.


  Routing-Spec: `yuno-team-routing`.

  '
trigger_keywords: ['linux', 'security', 'audit', 'secure', 'boot']
keywords: ['linux', 'security', 'audit', 'secure', 'boot']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['system-security-audit', 'claude-security-auditor', 'host-security-audit']
---

---

# Security Audit — Three-Layer Linux Security

Covers three security layers:
1. **Host/Hardware** — fwupd HSI, TPM, Secure Boot, kernel taint, power management
2. **System/Software** — ports, services, permissions, firewall, users
3. **Local AI Services** — Ollama install/removal, config sync, network exposure

## Layer 1: Host Security (Hardware + Firmware)

See `references/host-security-audit.md` for full guide.

### Quick Reference
```bash

set -euo pipefail
# HSI level
fwupdmgr security 2>&1 | head -30

# Kernel taint
cat /proc/sys/kernel/tainted

# Secure Boot
mokutil --sb-state

# TPM
ls /sys/class/tpm/tpm*

# Lockdown
cat /sys/kernel/security/lockdown
```

### HSI Levels
| Level | Meaning | Common Items |
|-------|---------|--------------|
| HSI-1 | UEFI Secure Boot, TPM 2.0, ME locked | UEFI PK, Boot Services Vars, MEI |
| HSI-2 | Intel BootGuard, IOMMU | BootGuard Fuse, IOMMU, Platform Debug |
| HSI-3 | Suspend, DMA Protection, CET | Suspend To Idle, Pre-boot DMA |
| HSI-4 | Maximum (server-class) | Encrypted RAM (TME/MKTME) |

### Suspend To Idle Fix (HSI-3)
Four configs needed:
1. Kernel: `mem_sleep_default=s2idle` in cmdline
2. systemd: `/etc/systemd/sleep.conf.d/s2idle.conf` with `SuspendState=mem`
3. logind: `/etc/systemd/logind.conf.d/s2idle.conf` with `HandleLidSwitch=suspend`
4. GNOME: `gsettings set org.gnome.settings-daemon.plugins.power lid-close-suspend-with-external-monitor true`
5. Refresh: `kill -USR1 $(pgrep gsd-power)`

### Kernel Taint Triage
| Bit | Name | Common Cause |
|-----|------|--------------|
| 0 | PROPRIETARY_MODULE | NVIDIA, ZFS, VirtualBox |
| 12 | STALE_HW | ACPI BIOS errors, firmware-DMI mismatch |

## Layer 2: System Security (Software)

See `references/system-security-audit.md` for full guide.
See `references/gcp-ubuntu-hardening.md` for Google Cloud Ubuntu VM hardening: OS Login, restrictive GCP firewall + UFW, Shielded VM, encryption model decisions, Ops Agent, snapshots, and performance baseline before tuning.

### Quick Reference
```bash

set -euo pipefail
# Firewall + ports
sudo ufw status
ss -tlnp | grep -E "0\.0\.0\.0:|:::"

# Permissions
ls -la ~/.hermes/state.db ~/.hermes/config.yaml ~/.ssh/
ls -la ~/.hermes/logs/ ~/.hermes/state-snapshots/

# Services
systemctl list-units --type=service --state=running | head -30

# Users
sudo cat /etc/passwd | grep -E "/home|/bin/bash" | cut -d: -f1,3,7

# Updates
apt list --upgradable 2>/dev/null | grep -c "/"
```

### Quick-Fix Cheatsheet
```bash

set -euo pipefail
# Dienst deaktivieren
sudo systemctl stop <dienst> && sudo systemctl disable <dienst>

# Häufige Dienste mit Sicherheitsrisiko
sudo systemctl disable --now gnome-remote-desktop.service  # RDP auf *:3389
sudo systemctl disable --now zramswap.service              # legacy, wenn systemd-zram-generator aktiv
sudo systemctl disable --now zram-config.service           # legacy, wenn systemd-zram-generator aktiv

# Port auf localhost beschränken
sudo ufw deny <port>/tcp
sudo ufw allow from 127.0.0.1 to any port <port> proto tcp

# Service-Bindung prüfen (ss -tlnp) vs. Firewall (ufw status) unterscheiden.
# Ein Dienst kann auf *:3389 lauschen, auch wenn UFW von außen blockt.
# Besser: Dienst auf 127.0.0.1 binden oder deaktivieren.

# Berechtigungen korrigieren
chmod 600 ~/.hermes/state.db ~/.hermes/kanban.db ~/.hermes/config.yaml
chmod 700 ~/.ssh/ ~/.hermes/state-snapshots/

# Hermes-spezifisch
chmod 600 ~/.hermes/logs/agent.log ~/.hermes/logs/errors.log
find ~/.hermes/state-snapshots/ -type f -exec chmod 600 {} \;

# Prüfen ob zram via systemd-generator läuft (alternativ zu legacy zramswap)
systemctl status systemd-zram-setup@zram0.service --no-pager 2>/dev/null | head -3
zramctl | grep -E 'ALGORITHM|^/dev' || true

# Leere Passwörter prüfen
sudo awk -F: '($2==""){print "EMPTY_PASSWORD:"$1}' /etc/shadow

# NOPASSWD sudo-Einträge prüfen
sudo grep -RIn NOPASSWD /etc/sudoers /etc/sudoers.d/ 2>/dev/null || echo "none found"
```

### Git Remote Token Leak Detection (Layer 2, ab 2026-07-05)

**Kontext:** GitHub-Tokens (`gho_`, `ghp_`, `ghs_`) oder OpenAI-Keys (`sk-`) werden häufig versehentlich in Git-Remote-URLs embedded, wenn ein Entwickler per `git clone https://username:TOKEN@github.com/...` klont statt via SSH oder Credential-Helper.

**Scan-Befehl über alle lokalen Repos:**

```bash

set -euo pipefail
echo "=== Token-Leak Scan ==="
find ~ -name ".git" -type d -prune 2>/dev/null | while IFS= read -r gitdir; do
  repo=$(dirname "$gitdir")
  remote_url=$(git -C "$repo" remote get-url origin 2>/dev/null || true)
  if echo "$remote_url" | grep -qE '(gh[ops]|ghu|sk-)[A-Za-z0-9_-]{20,}'; then
    token=$(echo "$remote_url" | grep -oE '(gh[ops]|ghu|sk-)[A-Za-z0-9_-]{20,}')
    echo "🚨 TOKEN LEAK: $repo"
    echo "   URL: $remote_url"
    echo "   Token: ${token:0:10}...${token: -4}"
  fi
done

echo ""
echo "=== Aktive Token-Prüfung ==="
gh auth status --show-token 2>&1 | head -5
```

**Wenn Token aktiv ist (API-Antwort 200 auf `/user`):**
1. Token aus remote URL entfernen: `git remote set-url origin git@github.com:OWNER/REPO.git`
2. Token REVOKEN im Browser: https://github.com/settings/tokens — prüfe ob `gh` den gleichen Token verwendet: `gh auth status --show-token`
3. Falls identisch: `gh auth logout` + `gh auth login` neu (erzeugt neuen Token)

**Secret-Detection vor jedem Commit (Quick-Check für Dirty-Files):**

```bash

set -euo pipefail
git diff --cached --name-only 2>/dev/null | while IFS= read -r file; do
  if [ -f "$file" ]; then
    found=$(grep -nE '(password[=: ]|token[=: ]|api.?key[=: ])' "$file" 2>/dev/null || true)
    if [ -n "$found" ]; then
      echo "⚠️ SECRETS in ${file}:"
      echo "$found"
    fi
  fi
done
```

### Local Config Secret Exfiltration Audit (Layer 2, ab 2026-07-11)

**Problem:** Secrets landen in `~/.hermes/config.yaml` (mcp_servers.*.env, provider-api-keys, GitHub-PATs) und duplizieren sich über Library-Clones, Worktrees, Backups und State-Snapshots — bis zu 6+ Kopien auf derselben Platte. Selbst wenn der Token revoked ist (HTTP 401), bleibt der String in 6 Files liegen → bei Backup-Sync, Cloud-Mount oder Repo-Push potenziell exponierbar.

**Found 2026-07-11:** GitHub-PAT `gho_2X...Lz1g` in `~/.hermes/config.yaml` Zeile 728, revokiert (HTTP 401). 6 Dateien auf Disk: Hauptkonfig + 3 Backups (`*.bak.*`, `*.pre-audit.*`, `*.corrupt.*`) + 3 Library-Copies (`~/30-Library/hermes-v7/`, `~/20-experimental/hermes-v7-wt/`, `~/40-archive/hermes-zorin/`). **Kein** Git-Commit in allen lokalen Repos bestätigt (`git log -S"gho_2XZO" --all` = leer).

#### Vollständige 5-Stufen-Verifikation

```bash

set -euo pipefail

# === Schritt 1: Token extrahieren (nur maskiert echoen!) ===
TOKEN=$(grep -oP '(?<=GITHUB_PERSONAL_ACCESS_TOKEN: )gho_[A-Za-z0-9]+' ~/.hermes/config.yaml | head -1)
[ -z "$TOKEN" ] && { echo "Token-Pattern nicht gefunden"; exit 1; }
MASK=$(echo "$TOKEN" | sed -E 's/(gho_[A-Za-z0-9]{4})[A-Za-z0-9]+([A-Za-z0-9]{4})/\1****\2/')
echo "Masked: $MASK (Länge: ${#TOKEN})"

# === Schritt 2: API-Status (LEBT der Token noch?) ===
echo "=== Schritt 2: API-Verifikation ==="
curl -sI -H "Authorization: token $TOKEN" \
  -H "User-Agent: yuno-audit" \
  https://api.github.com/user 2>&1 | grep -E '^(HTTP|X-OAuth-Scopes|x-oauth|github-authentication)'
# HTTP 200 → LIVE → P0. HTTP 401 → revoked → minimal risk.

# === Schritt 3: Git-History in ALLEN lokalen Repos ===
echo "=== Schritt 3: Git-History-Check ==="
find ~ -maxdepth 6 -name ".git" -type d \
  -not -path "*/.cache/*" -not -path "*/node_modules/*" \
  2>/dev/null | while read GITDIR; do
  REPO=$(dirname "$GITDIR")
  HITS=$(git -C "$REPO" log --all --source --oneline -S"${TOKEN:0:12}" 2>/dev/null | head -3)
  [ -n "$HITS" ] && echo "⚠️ Token committed in: $REPO → $HITS" || true
done

# === Schritt 4: Working-Tree Surface-Area ===
echo "=== Schritt 4: Surface-Area Scan ==="
for LOC in ~/.hermes/ ~/30-Library/ ~/10-Projekte/ ~/50-System/; do
  HITS=$(grep -rln "${TOKEN:0:12}" "$LOC" 2>/dev/null | head -10)
  if [ -n "$HITS" ]; then
    echo "  $LOC: $(echo "$HITS" | wc -l) Files mit Token-Prefix"
    echo "$HITS" | sed 's/^/    /'
  fi
done

# === Schritt 5: Backup-Files prüfen ===
echo "=== Schritt 5: Backup-Files mit Token ==="
find ~/.hermes/ -maxdepth 2 \( -name "*.bak*" -o -name "*.pre-*" -o -name "*.corrupt*" \) 2>/dev/null |\
  while read F; do grep -l "${TOKEN:0:12}" "$F" 2>/dev/null && echo "  Token in: $F" || true; done

# === Schritt 6: Permissions auf ALLEN Token-haltenden Files ===
echo "=== Schritt 6: Permissions ==="
for f in $(grep -rln "${TOKEN:0:12}" ~/.hermes/ 2>/dev/null); do
  perm=$(ls -la "$f" | awk '{print $1}')
  echo "  $perm $f"
done

unset TOKEN
```

#### Grep-Präzisions-Regel

`grep -rE "gho_"` fängt Test-Fixtures (z.B. `"gho_ab...1234"` in `test_copilot_auth.py`). Präzisions-Pattern für echte Tokens:
```
gho_[A-Za-z0-9_-]{30,40}
```
Echte GitHub-Tokens sind exakt 40 Zeichen (Präfix `gho_` + 36 alphanumerisch), enthalten KEINE Punkte und KEINE `...`. Ein `...` oder `.` im gefundenen String = Test-Fixture.

Verifiziert 2026-07-11: Breiter Scan zeigte 25+ Repos mit "Token gefunden". Präzisions-Scan reduzierte auf 5 echte Treffer — alle in `.hermes/config.yaml`-Copies (3 Library + 1 Haupt + 1 Backup).

#### Surface-Area-Risk-Assessment

| Befund | Risk | Maßnahme |
|--------|------|----------|
| **Token revokiert** (HTTP 401) | 🟢 Minimal — String ist tot | P2 Hygiene, nicht eilig |
| **Token in Git committed** (`git log -S` Hits) | 🔴 P0 Emergency | Token rotieren + Commit aus History entfernen |
| **Token in Working-Tree-Kopien** | 🟡 Lokal, Perms 600 | Bei Gelegenheit auf Env-Reference umstellen |
| **Token in Backups / Snapshots** | 🟡 Lokal | Backup-Cleanup in nächster Rotation |
| **Token in Cloud-Sync-Ordnern** (Nextcloud, Google Drive) | 🔴 Verteilungs-Risiko | Rotieren + Sync-Pfade auditen |

#### Remediation-Pattern: Env-Reference-Migration

```bash
# Statt Token-Plaintext in config.yaml:
#   GITHUB_PERSONAL_ACCESS_TOKEN: gho_2X...Lz1g
# Wird zu:
#   GITHUB_PERSONAL_ACCESS_TOKEN: ${GITHUB_PAT}
#
# Token lebt dann NUR in ~/.env (chmod 600) und wird via shell-Env geladen
```
Dieses Pattern gilt für ALLE Secrets in `~/.hermes/config.yaml`: Provider-Keys, MCP-Tokens, Bot-Tokens.

#### Unterschied zu Git-Remote-Token-Leak (oben)

- **Git-Remote-Token-Leak:** Token steckt in `git remote get-url origin` → Risiko: Git-Push/Hub-Sync.
- **Local-Config-Exfiltration:** Token steckt in `~/.hermes/config.yaml` → Risiko: lokale Copies (Library-Clones, Backups, Worktrees).

Beide prüfen, aber unterschiedliche Fix-Patterns (remote: `git remote set-url` + revoken; local: Env-Reference + Backup-Cleanup).

Siehe `references/secret-token-exfiltration-local-2026-07-11.md` für das vollständige Live-Protokoll der 2026-07-11 Session mit 6 gefundenen Kopien.

### Read-only Audit Mode

When the user asks for a local/read-only audit, do not apply fixes unless explicitly authorized. Run Layer 1-3 checks, write a prioritized report, and list exact fix commands separately.

Read-only workflow:
1. Capture host/firmware state (`fwupdmgr security`, Secure Boot, TPM, kernel taint, lockdown).
2. Capture system state (`ufw status`, listening TCP/UDP sockets, services, users, sudoers, updates, sensitive permissions).
3. Capture local AI service state (`which ollama`, user/system services, AI ports, Hermes config references).
4. Distinguish socket binding from firewall reachability: `*:3389` or `*:3000` is still a finding even if UFW denies public ingress.
5. Write `~/docs/system/security.md` unless the user explicitly forbids report writing.
6. Classify findings as P0/P1/P2/P3 and provide fix commands without executing them.

See `references/local-read-only-security-audit.md` for the report template and audit probes.

## Layer 3: Local AI Service Hygiene

See `references/local-ai-security-hygiene.md` for full guide.

### Ollama Binary & Service Removal (keep models)

If the user wants to keep model data (~/.ollama is often 10–80+ GB):

```bash

set -euo pipefail
# 1. Service stoppen und entfernen
systemctl --user stop ollama 2>/dev/null
systemctl --user disable ollama 2>/dev/null
rm -f ~/.config/systemd/user/ollama.service
systemctl --user daemon-reload

# 2. Binary (often a Symlink!)
rm -f ~/.local/bin/ollama
rm -rf ~/.local/lib/ollama

# 3. Network monitor / cron cleanup
rm -f ~/.local/bin/ollama_network_monitor.sh
crontab -l 2>/dev/null | grep -v ollama_network_monitor | crontab - 2>/dev/null

# 4. Snap-Reste
snap remove ollama 2>/dev/null

# 5. Verifikation
which ollama 2>/dev/null && echo "WARN: still present" || echo "✓ binary removed"
echo "Models preserved: $(du -sh ~/.ollama 2>/dev/null | cut -f1 || echo 'none')"
```

### Ollama Complete Removal (incl. models)

Only when the user explicitly says to delete all models:

```bash

set -euo pipefail
# Steps 1-2 identical
systemctl --user stop ollama 2>/dev/null
systemctl --user disable ollama 2>/dev/null
rm -f ~/.config/systemd/user/ollama.service
systemctl --user daemon-reload
rm -f ~/.local/bin/ollama
rm -rf ~/.local/lib/ollama

# 3. Modelle & Runtime-Daten (10–80+ GB!)
rm -rf ~/.ollama ~/.local/share/ollama /usr/share/ollama

# 4. Snap-Reste
snap remove ollama 2>/dev/null

# 5. Verifikation
which ollama 2>/dev/null && echo "WARN: still present" || echo "✓ completely removed"
```

### Hermes Config After Ollama Removal
```bash

set -euo pipefail
# Find all ollama references
grep -in "ollama" ~/.hermes/config.yaml

# Remove via Python (hermes config set can't handle lists/dicts)
python3 -c "
import yaml, pathlib
cfg = pathlib.Path.home() / '.hermes' / 'config.yaml'
with open(cfg) as f:
    data = yaml.safe_load(f)
data['providers'].pop('ollama-launch', None)
data['custom_providers'] = [cp for cp in data.get('custom_providers', [])
    if cp.get('name', '').lower() != 'ollama']
data['fallback_providers'] = [fp for fp in data.get('fallback_providers', [])
    if 'ollama' not in str(fp.get('provider', ''))]
if data.get('model', {}).get('api_key') == 'ollama':
    data['model']['api_key'] = ''
with open(cfg, 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
"
```

### 401 Error Root Cause
`model.api_key: ollama` in config.yaml → Hermes sends `Authorization: Bearer ollama` to API → 401.
**Fix:** `hermes config set model.api_key ''`

## Security Checklist
- [ ] Firewall active (`ufw status`)
- [ ] No unnecessary open ports on `0.0.0.0`
- [ ] `state.db`, `config.yaml`, logs at `600`
- [ ] `~/.ssh/` at `700`
- [ ] `state-snapshots/` at `700`
- [ ] No stale AI services running
- [ ] Hermes config has no dead provider references
- [ ] `security.redact_secrets` enabled
- [ ] `dm_policy` appropriate for use case
- [ ] Systemd linger enabled (`loginctl show-user $USER | grep Linger`)

## Pitfalls

### Snap Removal of Damaged Packages
- `snap remove` fails when a component.yaml is missing (corrupt snap).
- **Do NOT** manually edit `/var/lib/snapd/state.json` with `sed` — the file is JSON and removing matching lines corrupts the entire snapd state.
- Safe recovery when state.json gets corrupted:
  1. `sudo rm -f /var/lib/snapd/state.json`
  2. `sudo systemctl restart snapd`
  3. Reinstall critical snaps: `sudo snap install <name>` for gitea, code, core, google-cloud-cli, etc.
- Use `snap forget <snapname>` or check `snap changes` for in-progress operations before attempting manual cleanup.

### Ollama: Always Confirm Model Deletion
- `~/.ollama` is often 10–80+ GB. Users may want binary/service removed but models preserved.
- Offer the "soft remove" variant (binary + service only) before asking about model deletion.
- Hermes config cleanup (`api_key: ollama` → empty, remove provider refs) is independent of model data.

### Hermes Config: `api_key: ollama` Magic Value
- `model.api_key: ollama` causes 401 errors on real providers.
- Fix: clear to `api_key: ''` and remove dead provider references from `providers`, `custom_providers`, and `fallback_providers`.

### Permission Fix Order
- Fix permissions before restarting services: `chmod 600` on `state.db`, `kanban.db`, `config.yaml`; `chmod 700` on `state-snapshots/` + recursive file fix.

## References

- `references/secret-token-exfiltration-local-2026-07-11.md` — **NEU** Lokale Config-Secret-Exfiltration: 5-Stufen-Verifikation (API-Status, Git-History, Surface-Area, Backups, Permissions), Grep-Präzisions-Regel, Surface-Area-Risk-Assessment, Env-Reference-Migration-Pattern. Live-Evidence aus der 2026-07-11 Session mit 6 gefundenen Token-Kopien.\n- `references/host-security-audit.md` — Host security (HSI, TPM, Secure Boot, kernel taint, power)\n- `references/system-security-audit.md` — System security (ports, services, permissions, firewall)\n- `references/local-ai-security-hygiene.md` — AI service hygiene (Ollama removal, config sync)\n- `references/gcp-ubuntu-hardening.md` — Google Cloud Ubuntu VM hardening (OS Login, GCP firewall/UFW, Shielded VM, encryption decisions, Ops Agent, snapshots, performance guardrails)
