# MaxHermes-Cloud-Mesh — Praxisbeispiel (2026-07-08)

**Dauer:** ~90 Min
**Hosts:** 3 (Basti-Desktop + GCP-VPS + Alibaba-Cloud-Pod)
**Ergebnis:** Architektur-Review fertig, Tailscale-Mesh empfohlen (Score 4.65/5), Setup pausiert

## Host-Profil

| Host | Rolle | OS | Public-IP | Ingress? |
|------|-------|----|-----------|----------|
| `bratan-17-P1` | Basti-Desktop | Zorin OS 18.1 (Ubuntu 24.04), Kernel 6.17.0-35 | wechselnd (ProtonVPN, CGN) | ❌ NAT + CGN |
| `cloud-server` | GCP-VPS | Ubuntu 26.04 LTS | **34.159.58.43** (statisch) | ✅ |
| `maxhermes-4kjhd` | Cloud-Pod | Hermes Agent v0.9.0 in Container | keine (172.25.43.228 intern) | ❌ deny-all-ingress |

## Verbindungs-Matrix

| Von → Nach | Desktop | GCP | Pod |
|------------|---------|-----|-----|
| **Desktop** | — | ✅ gcloud-ssh | ❌ |
| **GCP** | ❌ (kein sshd, NAT) | — | ❌ |
| **Pod** | ❌ | ✅ sshd aktiv | — |

**Kernproblem:** Kein Pfad zum Pod — alle Lösungen müssen am Pod **ausgehend** starten.

## Evaluierte Optionen

| Option | Score | Setup | Robustheit |
|--------|-------|-------|------------|
| A GCP-Reverse-Tunnel | 3.65 | ~30 Min | 2/5 (GCP-SPOF) |
| **B Tailscale-Mesh** | **4.65** ⭐ | ~55 Min | 4/5 |
| C Cloudflare-Tunnel | 3.65 | ~10 Min | 3/5 |
| D Hybrid | 4.20 | ~75 Min | 5/5 |

## Use-Cases

- UC1: File-Sync Desktop ↔ Pod
- UC2: SSH in den Pod
- UC3: Pod als Heimnetz-Worker

## Schlüssel-Facts für künftige Sessions

1. **Kein sudo NOPASSWD** auf Basti-Desktop → Yuno kann Tailscale nicht autark installieren
2. **Pod hat kein systemd** → tailscaled muss manuell als Daemon gestartet werden (userspace-networking mode)
3. **GCP-VPS hat Ubuntu 26.04** (nicht 24.04 wie angenommen) — neuere Paket-Versionen
4. **Pod-Name:** `maxhermes-4kjhd`, Namespace `maxhermes`, Cluster `maxclaw.svc.cluster.local`
5. **docs/system/yuno/** enthält die 3 Markdown-Artefakte
6. **Bastis Dokument-Präferenz:** Fakten-basierte Architektur, keine langen Einleitungen. Host-Map und Verbindungs-Matrix zuerst.

## Status (2026-07-08)

- ✅ Phase 1 (Review) abgeschlossen
- ✅ Phase 2 (Evaluation) abgeschlossen
- ⏸️ Phase 3 (Setup) pausiert — Basti liest Master-Dokument, entscheidet dann

## Nächster Schritt

Basti liest `~/docs/system/yuno/yuno-architektur-mesh-2026-07-08.md` und gibt Go/No-Go für Phase 3.