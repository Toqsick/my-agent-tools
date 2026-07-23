# Cloud Hermes Deployment & Connectivity

Wenn Basti fragt „Geht SSH zu meiner Cloud-Instanz?" — Antwort hängt von der **Hosting-Architektur** ab, nicht nur vom sshd-Status auf der Instanz.

## Cloud-Archetypen & SSH-Möglichkeit

| Architektur | SSH-Inbound? | SSH-Outbound? | Beispiel |
|---|---|---|---|
| **K8s Pod / ECI** (Container ohne Service/Ingress) | ❌ Blockiert (Deny-All-Ingress, kein LB) | ✅ Ja (via NAT) | MiniMax MaxHermes Pod |
| **K8s Pod mit Service/LoadBalancer** | ✅ Ja (Port im Service exponiert) | ✅ Ja | Standard-K8s |
| **Cloud VM mit Public-IP** (GCP EC2 DO) | ✅ Ja (sshd + Firewall) | ✅ Ja | Bastis alter GCP-VPS |
| **Heimserver hinter NAT** | ⚠️ Port-Forwarding oder VPN | ✅ Ja | Zorin-OS-Desktop |

## SSH-Diagnose-Entscheidungsbaum (K8s-Pod-Szenario)

```
User: „Geht SSH zu meiner Cloud-Hermes-Instanz?"

1. LÄUFT SSH-SERVER AUF DER INSTANZ?
   → `systemctl is-active sshd` / `ps aux | grep sshd`
   → Falls NEIN: installieren + manuell starten
     (Container ohne systemd: `mkdir -p /run/sshd && /usr/sbin/sshd -D`)

2. HAT INSTANZ PUBLIC-IP ODER INGRESS?
   → `ip addr`: nur interne Cluster-IP → K8s-Pod ohne LB
   → `ss -tlnp`: sshd lauscht lokal, Inbound trotzdem blockiert
   → K8s-ECI ohne LoadBalancer = KEIN Inbound-SSH möglich

3. FALLS NEIN: WELCHER WORKAROUND PASST?
   → Siehe § Cloud-Workarounds unten
```

## Cloud-Workarounds (wenn Inbound-SSH blockiert)

| Workaround | Voraussetzung | Aufwand | Robustheit |
|---|---|---|---|
| **A. Reverse-Tunnel via VPS** | Server mit Public-IP + SSH-Key vom Pod auf Server authorized | ~30 Min | Mittel — bricht wenn Server down |
| **B. Tailscale/ZeroTier Mesh** | Auf Pod installierbar (root), Account (kostenlos bis 100 Devices) | ~45 Min | ⭐ **Hoch** — keine offenen Ports |
| **C. File-only Sync** (GitHub/MCP/Webhook) | Config per curl pushen, Skills per GitHub-Release sync | ~15 Min | Niedrig — kein Live-Terminal |
| **D. LoadBalancer beim Admin** | Cluster-Admin provisioniert Service + EIP | ~1 Ticket | Höchste — K8s-konform |

## Security

SSH-Keys niemals committen. Im Pod generieren, Public-Key manuell auf Zielserver setzen. `~/.ssh/` und `/etc/ssh/` vom Backup ausschließen.

## Setup-Report-Template (Hermes V7 Cloud-Assessments)

Bevorstehendes Template für Ist-Zustands-Dokumentation (zelebriert in Bastis `maxhermes-4kjhd`-Report):

```
# <TITEL> — <KONTEXT>
Erstellt: <Datum> · Instanz: <name>

## TL;DR
<3-5 Zeilen: läuft/nicht läuft/Reifegrad>

## 1. Cloud-Instanz: Hardware & Umgebung
### 1.1 Host-Identität · 1.2 Cluster-Kontext · 1.3 Netzwerk

## 2. Hermes-Konfiguration
### 2.1 Version & Runtime · 2.2 Model & Provider · 2.3 Toolsets
### 2.4 Sicherheit · 2.5 MCP-Server

## 3. Verzeichnis-Struktur & Persistenz
### 3.1 Workspace & Hermes-Home · 3.2 Memory · 3.3 Doku

## 4. Installierte Tools & CLI-Agents
### 4.1 Externe Agents (Login-Status) · 4.2 Standard-Tools

## 5. Multi-Agent-Architektur-Status
### 5.1 delegate_task funktioniert? · 5.2 Muster · 5.3 Lücken

## 6. Reifegrad-Selbsteinschätzung (1-5)
### 6.1 Scorecard · 6.2 was läuft · 6.3 ehrliche Lücken

## 7. Nächste Schritte (Prio 1 / 2 / 3)

## 8. Anhang: System-Vars, Subagent-Tests, K8s-Indikatoren

## 9. Fazit
```

## Git-Based Sync (when SSH/VPN is impossible)

Wenn ein Cloud-Pod **keinen Ingress erlaubt** (Alibaba ECI, K8s Pod ohne Service/LB), aber HTTPS-Outbound funktioniert → **Git als Transport-Layer**.

### Kern-Patterns (erprobt am MaxHermes Cloud Pod, 2026-07-08):

| Pattern | Beschreibung |
|---------|-------------|
| **Branch als Config-Portal** | Dedizierter Branch im bestehenden Hermes-Repo (kein separates Repo) |
| **Sanitisierte Config-Templates** | Configs ohne echte Keys/Tokens — Platzhalter verweisen auf `.env` |
| **Pod pullt via Cron** | `git pull --ff-only` stündlich, Skripte liegen im Branch |
| **GitHub Actions validieren** | YAML-Lint, ShellCheck, Markdown-Links bei jedem Push auf den Branch |
| **Review → Evaluate → Setup** | Dreiphasiger Workflow: Ist-Zustand erfassen, Scorecard, dann sauber bauen |

### Architektur

Desktop → `git push` → GitHub Branch → `git pull` (Cron) → Cloud Pod.  
Kein SSH, kein VPN, kein LB — nur HTTPS-Outbound vom Pod.

### Wann Git statt SSH/VPN

Wenn der Pod Deny-All-Ingress hat (ECI) und kein LoadBalancer provisioniert werden kann. Git-Sync ist weniger interaktiv als SSH, aber zuverlässig und **einmal eingerichtet wartungsfrei**.

→ See `references/cloud-git-sync.md` für das vollständige ausgearbeitete Beispiel (Branch-Struktur, Skripte, Workflows, Pitfalls).