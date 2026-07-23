---
title: "01 — Server-Hardening"
tags: [workflow-template, hardening, server, security, linux, ubuntu]
aliases: ["Hardening-Template", "Server-Sec"]
parent_skill: workflow-template
---

# Template 01: Server-Hardening (Homelab / VPS / Cloud)

> **Bewertung**: ⭐⭐⭐⭐⭐ — Das ausgereifteste Template. Multi-Agent, Ethics-by-Design, Lockout-Schutz.

## Profile

| Profil | Trigger |
|--------|---------|
| `medion-laptop` | Eigenes Laptop (zorin-medion) |
| `cloud-vm` | GCP/AWS/Hetzner-Instanz |
| `homelab` | Self-Hosted NAS/Server |
| `production` | Live-Traffic-System |

## Orchestrator-Rolle

Du bist ein Multi-Agent-Orchestrator für Linux-Server-Hardening. **Kein Werkzeugzugriff auf das reale System!** Simulierte Sub-Agenten erzeugen einen vollständigen, geprüften Hardening-Plan. Jede tatsächliche Ausführung (Config-Änderung, Service-Restart) erfolgt in einer separaten, genehmigten Phase außerhalb der Plan-Erstellung.

## Sub-Agenten (sequenziell + zwei Parallel-Stufen)

| # | Agent | Aufgabe | Output | Layer |
|---|-------|---------|--------|-------|
| 0 | **SCOPE-GUARDIAN** | Definiert Anwendungsbereich + Autorisierung | Scope-Freigabe ODER Abbruch | Sequential |
| 1 | **ATTACK-SURFACE-SCANNER** | Fragt Systemdetails ab | Angriffsflächen-Liste | Sequential |
| 2 | **HARDENING-ANALYST** | Schlägt Massnahmen vor | Massnahmen-Katalog mit Risiko/Aufwand | Parallel zu 2b |
| 2b | **ROLLBACK-ARCHITECT** | Backup-Medium, Restore-Pfad, Test-Verify pro Massnahme | Rollback-Checkliste pro Schritt | Parallel zu 2 |
| 3 | **AVAILABILITY-REVIEWER** | Lockout-Risiko-Prüfung pro Vorschlag | Lockout-Score + zweite-Session-Anforderung | Parallel zu 3b |
| 3b | **TEST-PLANNER** | Test-Kommando + Erwartetes Ergebnis pro Massnahme | Verify-Tabelle | Parallel zu 3 |
| 4 | **DOCUMENTATION-ARCHITECT** | Doku-Struktur (Checkliste, Testplan, Troubleshooting) | Doku-Template | Sequential |
| 5 | **CRITIC / FINAL-REVIEWER** | Konsolidierung + Konsistenz-Check | Final-Plan oder Rückgabe | Sequential |

## Ablauf

```
SCOPE-GUARDIAN
    ↓
ATTACK-SURFACE-SCANNER
    ↓
HARDENING-ANALYST  +  ROLLBACK-ARCHITECT     (delegate_task parallel)
    ↓
AVAILABILITY-REVIEWER  +  TEST-PLANNER      (delegate_task parallel)
    ↓
DOCUMENTATION-ARCHITECT
    ↓
CRITIC / FINAL-REVIEWER → Freigabe
```

## Harte Regeln (zwingend)

- 🟥 Kein Agent ändert reale Konfigurationen — **nur Plan-Ausgabe!**
- 🟥 **Scope-Freigabe VOR allem anderen** — ohne Scope-Bestätigung Abbruch
- 🟥 **Reihenfolge zwingend**: Zugang sichern → Firewall → Dienste härten (verhindert Lockout)
- 🟧 Jede zugangsrelevante Änderung (SSH, Firewall, sudo) braucht **Backup + zweite offene Session**
- 🟧 Snapshot VOR Block (LVM/ZFS/Btrfs), Verify NACH Block (Testplan abgehakt)
- 🟨 Audit-Trail: `lynis` oder `OpenSCAP` nach Hardening als Compliance-Proof

## Pitfalls (Hardening-spezifisch)

- ⚠️ `ufw disable` als vermeintlicher Schritt ohne zweiten Zugang → Lockout
- ⚠️ `PermitRootLogin no` ohne funktionierenden `sudo`-User → Ausgesperrt
- ⚠️ Firewall-Regel auf Remote statt lokal ändern → aussperren
- ⚠️ AppArmor/SELinux-Profile ohne Test aktivieren → Apps crashen ohne erkennbare Ursache
- ⚠️ SSH-Config ohne `sshd -t` Syntax-Test → kaputte Config wird gespeichert
- ⚠️ `systemctl` ohne `daemon-reload` bei Unit-Änderungen → Service startet nicht

## Profile-spezifische Hinweise

### `medion-laptop` (Bastis Setup)

- Single-User-System (`bratan`), keine Multi-Tenancy
- Wayland-Session (Xwayland crasht manche Tools) → X11-Login bevorzugen für Coolbits/GWE
- GPU-Sharing mit Gaming → dGPU-Calls nur vor Hardening
- WPA3-WLAN bei Mobility wichtig

### `cloud-vm`

- Öffentliche IPs → fail2ban zwingend
- SSH nur via SSH-Keys (`PasswordAuthentication no`)
- `unattended-upgrades` einrichten
- Cloud-Init-Remnant-Files prüfen (`/var/lib/cloud/`)

### `homelab`

- LAN-Trust höhere Schwelle als WAN
- DLNA/UPnP-Services wie rygel ggf. deaktivieren (LAN-facing listeners)
- regelmäßige Snapshot-Strategie via Snapper/ZFS-auto

### `production`

- **Immer** Wartungsfenster mit User-Notification
- Blue-Green-Deployment wo möglich
- Rollback-Plan mit gemessener RTO < 1h
- Canary-Test mit 5% Traffic vor Voll-Rollout

## Beispiel-Block (SSH-Hardening)

```markdown
## 🟥 Block 1: SSH-Zugang härten

### VORHER
- [ ] Zweite SSH-Session offen (Port-Forward testen)
- [ ] Backup: `sudo cp /etc/ssh/sshd_config /root/backups/sshd_config.$(date +%Y%m%d_%H%M%S)`
- [ ] LVM-Snapshot des Systems (`sudo lvcreate -L 5G -s -n snap-pre-ssh /dev/vg0/root`)

### DURCHFÜHREN
- `sudo nano /etc/ssh/sshd_config`
- Setze: `PermitRootLogin no`, `PasswordAuthentication no`, `Port 22 → 2222`
- `sudo sshd -t` (Syntax-Check, exit 0 erwartet)
- `sudo systemctl restart sshd`

### VERIFY
- [ ] `ssh -p 2222 user@localhost` von zweiter Session → muss klappen
- [ ] `ssh -p 22 user@localhost` → muss FAILEN
- [ ] `sudo journalctl -u sshd -n 50` → keine Errors

### ROLLBACK
- `sudo cp /root/backups/sshd_config.<ts> /etc/ssh/sshd_config && sudo systemctl restart sshd`
- Snapshot zurückrollen: `sudo lvconvert --merge /dev/vg0/snap-pre-ssh`
```

## Mnemosyne-Hook (nach Session)

Siehe `references/meta/mnemosyne-hooks.md` → Template 01.

Standard:
```python
mnemosyne_remember(
    content="Server-Hardening Session <system-name>: angewendet=<blocks>, Tests bestanden=<ja/nein>, Restrisiko=<offene-punkte>",
    importance=0.7, source="security-audit", extract_entities=True, veracity="tool"
)
```
