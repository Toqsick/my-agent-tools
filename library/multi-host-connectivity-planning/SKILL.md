---
name: multi-host-connectivity-planning
title: Multi-Host-Connectivity-Planning
description: >-
  Use when user asks for connecting multiple hosts, reviewing infrastructure connectivity architecture, comparing SSH, mesh, or tunnel options, or writing a cross-host setup playbook. NOT for configuring only one server or debugging container-internal networking. Uses a three-phase inventory, scored evaluation, and implementation playbook with ownership, validation, and rollback concerns.
version: '1.0'
created: '2026-07-08'
author: Yuno
trigger: when Basti wants to connect multiple hosts, set up mesh networking, evaluate connectivity options between servers, or plan multi-host infrastructure
license: MIT
trigger_keywords: ['playbook', 'and', 'multi-host-connectivity-planning', 'connecting', 'multiple']
keywords: ['playbook', 'user', 'asks', 'connecting', 'multiple']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---


# Multi-Host-Connectivity-Planning (3-Phasen-Methodik)

## Trigger

Dieser Skill wird geladen bei Aufgaben wie:
- "Verbinde meine Hosts miteinander"
- "Wie kriege ich Zugriff auf Pod/Server X?"
- "Architektur-Review für meine Infrastruktur"
- "Welche Lösung ist besser: A oder B?"
- "Setze mir SSH/Mesh/Tunnel zwischen Hosts auf"

## Anti-Trigger (nicht hier)

- **Einzelner Host:** Nur einen Server konfigurieren → `system-documentation`, `linux-system`
- **Reine Netzwerk-Diagnose** ohne Verbindung zwischen Hosts → `linux-system`
- **Container-internes Netzwerk** (Docker Compose, Kubernetes) → andere Skills
- **Bereits bestehende Verbindung optimieren** → `deployment-landing-zone`

## Workflow: 3 Phasen

### Phase 1 — Ist-Zustand erfassen

Erstelle eine **Host-Map** mit diesen Feldern für jeden Host:

| Host | Rolle | OS | Public-IP | Eingehend erreichbar? |
|------|-------|----|-----------|------------------------|

**Mindest-Checks pro Host:**
- OS + Kernel (`cat /etc/os-release`, `uname -a`)
- Netzwerk-Interfaces (`ip addr`, `ip route`)
- DNS-Resolver (`systemd-resolve --status` oder `/etc/resolv.conf`)
- UFW / Firewall-Status (`sudo ufw status`, `iptables -L -n`)
- SSH-Server/Client-Status (`which sshd`, `systemctl is-active ssh`)
- Public-IP via externem Service (`curl -4 ifconfig.co`)
- VPN-Status (wg-quick, ProtonVPN, tailscale etc.)
- Docker-Bridges (`docker network ls`, `brctl show`)

**Dokumente bekannte Einschränkungen:**
- Carrier-Grade-NAT → kein direkter Ingress möglich
- deny-all-ingress Network-Policy in Cloud-Containern
- Kein systemd (Container) → Daemon-Management anders
- Kein passwortloses sudo

**Zusätzlich: Verbindungs-Matrix erstellen**

Wer kann aktuell wohin verbinden?

| Von → Nach | Host A | Host B | Host C |
|------------|--------|--------|--------|
| Host A | — | ✅/❌ | ✅/❌ |
| Host B | ✅/❌ | — | ✅/❌ |
| Host C | ✅/❌ | ✅/❌ | — |

**Kritischen Befund identifizieren:** Gibt es einen Host ohne eingehenden Pfad? Das ist das Kernproblem.

### Phase 2 — Evaluation (Scorecard)

**2.1 Lösungswege sammeln**

Typische Kandidaten für Host-Verbindung:
1. **SSH-Reverse-Tunnel** (autossh über Bastion-Host)
2. **Tailscale/ZeroTier/WireGuard-Mesh** (P2P-VPN)
3. **Cloudflare-Tunnel** (outbound)
4. **VPN zu VPN** (z.B. ProtonVPN Site-to-Site)
5. **Hybrid-Kombination** z.B. Tailscale + Reverse-Tunnel-Fallback

**2.2 Kriterien-Matrix erstellen**

Typische Kriterien (anpassen pro Projekt):

| # | Kriterium | Gewicht | Begründung |
|---|-----------|---------|------------|
| 1 | **Erreichbarkeit** | 30 % | Ohne das funktioniert gar nichts |
| 2 | **Robustheit** | 20 % | Weniger Frickelei im Betrieb |
| 3 | **Sicherheit** (keine offenen Ports) | 15 % | Security-Hygiene |
| 4 | **Einrichtungs-Aufwand** | 10 % | Invertiert: 5=minimal |
| 5 | **Wartungs-Aufwand** | 10 % | Invertiert: 5=minimal |
| 6 | **Use-Case-Abdeckung** | 10 % | 3 UC's definieren |
| 7 | **Provider-Unabhängigkeit** | 5 % | Falls Cloud-Provider wechselt |

**2.3 Use-Cases (UC's) definieren**

Immer 3 Use-Cases definieren bevor du evaluierst:
- UC1: File-Sync (z.B. Desktop → Pod/Server)
- UC2: SSH-Zugriff (Remote-Shell)
- UC3: Worker (Pod greift auf Local-Ressourcen zu / Heimnetz-Integration)

**2.4 Scorecard ausfüllen**

Bewertung 1-5 (5 = beste), Gewichtung × Score = gewichteter Score.

| Kriterium | Gewicht | A: Tunnel | B: Mesh | C: Cloud | D: Hybrid |
|-----------|---------|-----------|---------|----------|-----------|
| ... | X % | Score | Score | Score | Score |

**Summe gewichtet** = Σ(Gewicht × Score) / 100

### Phase 3 — Setup-Playbook

**Struktur (Schritt-für-Schritt mit Verification):**

```
### Schritt N: <Name> (<Wer>, ~X Min)
  
**Befehl:**
bash script

**Verifikation:**
- ✅ Was muss danach true sein?

### Schritt N+1 ...
```

**Aufgabenverteilung dokumentieren:**
- Wer macht was? (Basti = User, Yuno = Agent)
- Dauer pro Schritt
- Welche Schritte brauchen sudo (User-Eingriff)?
- Welche Schritte kann Yuno autark machen?

**Failover-Sektion (Pflicht!):**
- Szenario: Primär-Lösung down → Workaround A/B/C
- Recovery-Schritte pro Ausfallszenario

**Monatliche Wartungs-Checkliste:**
- Was muss regelmäßig geprüft werden?
- Ablaufdaten von Keys/Tokens dokumentiert?

### Dokumente-Struktur

Dateien in `~/docs/system/<skill>/` ablegen (siehe `references/` für Vorlage):

| Datei | Inhalt |
|-------|--------|
| `README.md` | Index mit Status + Verweise |
| `<name>-review-YYYY-MM-DD.md` | Phase 1 |
| `<name>-evaluation-YYYY-MM-DD.md` | Phase 2 |
| `<name>-master-YYYY-MM-DD.md` | **MASTER**: Review + Evaluation + Playbook |

## Pitfalls (gesammelt aus der Praxis)

- ❌ **Kein passwortloses sudo auf Basti-Desktop:** Yuno kann Tailscale/etc. nicht autark installieren. Vorher checken, Basti bitten Schritt auszuführen.
- ❌ **Container ohne systemd:** `tailscaled` muss manuell gestartet werden. Workaround im Playbook dokumentieren (Cron, Healthcheck, userspace-networking).
- ❌ **Vergessene ACL-Konfiguration:** Tailscale installiert → Hosts sehen sich nicht automatisch. ACL-Check direkt nach Installation einbauen.
- ❌ **Auth-Key nicht rotiert:** Nach 90 Tagen abgelaufen, kein Verbindungsaufbau mehr möglich. Kalender-Erinnerung oder Pre-Auth-Key mit Verfallsdatum dokumentieren.
- ❌ **Shell-History mit Auth-Keys:** `history -c` nach Auth-Key-Usage empfehlen.
- ❌ **Docs liegen zu weit auseinander:** Review und Playbook in getrennten Dateien → Findet keiner wieder. Master-Dokument konsolidiert alles.
- ❌ **Vergessener GCP-VPS:** Läuft weiter, kostet ~$50/Monat. Wartungs-Checkliste erwähnt das.
- ❌ **Zu viel Einleitungs-Geblubber:** Basti will **faktenbasierte Architektur**, keine langen Einleitungen. Starte mit Host-Map und Verbindungs-Matrix.
- ❌ **Nicht verifizierte Annahmen:** OS-Version, sshd-Status, UFW-Regeln. Mit Live-Commands prüfen, nie aus Gedächtnis oder alter Doku übernehmen.

## Verifikation (vor Abschluss)

- [ ] Alle 3 Phasen durchlaufen?
- [ ] Ist-Zustand mit Live-Befehlen verifiziert (keine Annahmen)?
- [ ] Use-Cases definiert?
- [ ] Scorecard ausgefüllt mit ≥ 5 Kriterien?
- [ ] Setup-Playbook enthält:
  - [ ] Wer macht was (Basti/Yuno)?
  - [ ] Dauer pro Schritt?
  - [ ] Verification-Schritte?
  - [ ] Failover-Szenarien?
  - [ ] Wartungs-Checkliste?
- [ ] Dokumente in `~/docs/system/<skill>/` abgelegt?
- [ ] Memory-Update gemacht (Session-übergreifende Facts)?

## Referenzen

Siehe `references/` für Session-spezifische Details.
Siehe Templates in `templates/` für wiederverwendbare Strukturen.
Siehe Scripts in `scripts/` für automatisierte Prüfungen.

**Aktuelle Session-Artefakte:**
- `references/maxhermes-pod-2026-07-08.md` — Erst-Implementation, MaxHermes-Cloud-Mesh
- `references/hermes-android-hybrid-2026-07-10.md` — Hermes-Android Hybrid-Hosting (Workstation + cloud-server + Tailscale/Caddy), Architektur validiert, Setup-Plan in 4 Phasen mit Failure-Modi

## Verwandte Skills (Cross-References)

- `messaging-gateway-setup` SKILL.md "ZWEI verschiedene Gateway-Begriffe"-Warnbox + `references/api-server-quirks.md` — wenn Hybrid-Setup einen **API-Server** (Port 8642) braucht, dort reinlesen. Der hier dokumentierte Hermes-Android-Fall ist der häufigste Anlass.
- `github-workflow` SKILL.md "ALLE drei GH-Tools tot"-Pitfall — wenn im Recon-Schritt plötzlich kein GH-Tool mehr geht, ist `git clone --depth 1 https://...` der Read-Only-Fallback.