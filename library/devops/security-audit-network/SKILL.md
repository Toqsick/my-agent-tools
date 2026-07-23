---
name: security-audit-network
title: "Security Audit — Network + API Services"
description: "Use when auditing HTTP API services, network connections, open ports, or running connection-drop audits. NOT for host-layer hardening (use security-audit-host)."
category: devops
version: '1.0'
created: '2026-07-23'
author: Yuno (split from system-security-audit)
lane: koenigin
agent: universal
trigger_keywords: ['network', 'http', 'api', 'connection', 'port', 'service', 'session-monitoring']
keywords: ['network', 'api', 'connection', 'port', 'audit', 'cloud-agent']
related_skills: ['security-audit-host', 'security-audit-secrets']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from system-security-audit 2026-07-23)'

license: MIT
---

# Security Audit — Network + API Services

_Extracted from system-security-audit on 2026-07-23._

## Layer 4: Network Service Security Audit (HTTP API Services)

**Scope:** Security-Posture eines laufenden HTTP-Dienstes — Port-Bindung, Auth-Mechanismus, Route-Exposure, Configuration-Source-Tracing, Prozess-Lifecycle.

**Wann triggern:** User meldet einen Service auf Port X, die Frage kommt "ist das sicher?" oder "ist das ein P0-Befund?". Oder periodischer Audit exponierter Services.

**Abgrenzung zu Layer 1-3:** Layer 4 ist kein Host- oder System-Audit, sondern ein **Service-in-the-Large**-Audit — du hast einen laufenden Service (PID + Port) und musst wissen ob er bewusst exponiert ist oder ein Befund vorliegt.

### Phase 1: Live Route Probing

Jeden Endpoint ohne Auth-Header anlaufen:

```bash

set -euo pipefail
for path in / /api /health /health/detailed /v1/health /v1/models /v1/toolsets /v1/skills /v1/capabilities /api/sessions; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "http://127.0.0.1:$PORT$path" 2>/dev/null || echo "TIMEOUT")
  echo "$code  GET $path"
done
```

**Dokumentieren als Tabelle:** Method + Path + Status + Body-Preview + Auth-Req.
**Pitfalls:**
- `/health/detailed` vs `/health` — der rich-Endpoint disclosure PID/Uptime/Platform = Finding unter Auth
- Server-Header checken: `curl -sI <path> | grep -i "^server:"` → Framework + Version
- 5s-Timeout setzen — hängende Endpoints blockieren nicht den Scan

### Phase 2: Configuration Source Tracing

Finde **wo** Port-Bindung, Auth und Host-Konfiguration herkommen:

1. **Prozess-Start** → `ps -o pid,ppid,lstart,cmd -p $PID`
2. **Systemd-Unit** → `systemctl --user cat <service>.service`
3. **Config-File** → `grep -n -E 'api_server|port|host|bind|key' config.yaml`
4. **Environment** → `strings /proc/$PID/environ | grep -E 'API_SERVER|PORT|KEY' | sed 's/=.*/=<redacted>/'`
5. **Code-Defaults** → `grep -n 'DEFAULT_HOST\|DEFAULT_PORT' /pfad/zum/code.py`

### Phase 3: Auth Mechanism Verification

1. **Middleware- oder Handler-Level?** → `grep -n '_check_auth\|auth_middleware' source.py`
2. **Key-Vergleich** → `grep -B2 -A5 'def _check_auth' source.py` — nur `hmac.compare_digest` ist constant-time
3. **Bypass-Bedingungen** → `grep -B3 'if not self._api_key' source.py` — leerer Key = Fail-Open?
4. **Fail-Open/Fail-Closed?** → `grep -A3 'except.*Exception' source.py` — `return None` bei Exception = P0
5. **Logging jedes Rejects** → werden peer_ip, method, path, user_agent geloggt?

### Phase 4: Network Exposure Assessment

```bash

set -euo pipefail
echo "=== ALL INTERFACES ==="; ip -4 -o addr show | awk '{print $2, $4}'
echo "=== LISTENING ON ==="; ss -tlnp | grep ":$PORT"
echo "=== FIREWALL ==="; sudo ufw status 2>/dev/null | head -5
# Tailscale only:
command -v tailscale &>/dev/null && echo "=== TAILSCALE ==="; tailscale serve status 2>/dev/null; tailscale funnel status 2>/dev/null
```

**Bewertungsmatrix:**

| Bindung | Firewall | Risiko |
|---------|----------|--------|
| `127.0.0.1` | egal | ✅ Kein Risiko |
| `0.0.0.0` | Port auf Tailscale beschränkt | 🟡 Bewusst, wenn Auth aktiv |
| `0.0.0.0` | Keine Regel (LAN offen) | ⚠️ P1 — Multilayer-Exposure |
| `0.0.0.0` | Kein Auth | 🔴 P0 — Open Bar |

### Phase 5: Process Lifecycle Tracking

```bash

set -euo pipefail
echo "Boot:" $(who -b | awk '{print $3,$4}')
echo "Start:" $(ps -o lstart= -p $PID)
echo "Auto/Manual: $([ $(who -b | awk '{print $3,$4}' | date +%s -f -) -lt $(ps -o lstart= -p $PID | date +%s -f -) ] && echo 'MANUAL' || echo 'AUTO')"
```

**Start ≈ Boot** (< 3 min) → Auto-Start. **Start >> Boot** (> 30 min) → Manuelle Reaktivierung. PPID = bash → manuell aus Terminal. PPID = systemd → systemd-gesteuert.

### Phase 6: Risk Classification

| Severity | Bedeutung |
|----------|-----------|
| **P0** | Auth nicht aktiv oder Fail-Open. Dienst ohne Schutz auf 0.0.0.0. |
| **P1** | Auth vorhanden aber dünne Schutzlinie. 0.0.0.0 ohne Firewall. RCE-Risiko bei Token-Leak. |
| **P2** | Konfigurations-Hygiene. Kein akutes Risiko. |
| **P3** | Nice-to-have. Version-Disclosure, Logging-Hygiene. |

**Nie auto-fixen — immer Bericht dann Optionen A/B/C/D.**

#### P0-Downgrade Pattern (validiert 2026-07-16 Gateway Audit)

**Problem:** Ein neu entdeckter World-Listener auf `0.0.0.0:PORT` sieht aus wie ein klassisches P0 („Offener Port ohne Auth"). Der erste Reflex ist Panik. Aber der Server kann auth-geschützt UND `0.0.0.0` bewusst sein (= tatsächlich P2/P3, kein P0).

**Richtige Stufung — nicht reflexhaft P0 setzen:**

```
    World-Listener auf 0.0.0.0:PORT gefunden
        │
        ├─ Auth aktiv? (Bearer, hmac, signiert?)
        │   ├─ JA → KEIN P0 für Exposure allein
        │   │      │
        │   │      ├─ Bind bewusst gewollt? (Tailscale-Hybrid, dokumentiert)
        │   │      │   ├─ JA → P3 (beobachten)
        │   │      │   └─ UNKLAR → P2 (dokumentieren und klären)
        │   │      │
        │   │      └─ LAN offen? (UFW keine Regel für Port)
        │   │          ├─ JA → P1 (Firewall-Fronting fehlt)
        │   │          └─ NEIN → P2 (bereits geschützt)
        │   │
        │   └─ NEIN → P0 (akute Sicherheitslücke)
        │
        └─ Health-Endpoints? (/health, /v1/health)
            └─ Oft absichtlich public-by-design für Load-Balancer
               → kein Finding, solange /health/detailed auth-geschützt ist
```

**Praxistest (2026-07-16):** Gateway auf `0.0.0.0:8642` sah initial nach P0 aus. Biene-1 fand: Bearer-Auth via `hmac.compare_digest` enforced (11 Endpoints geprüft, alle außer 2× /health gaben 401). Bind `0.0.0.0` war bewusst für Tailscale-Serve-Android-Hybrid (`pending/memory/838383b3.json`). Echter Befund: **P1, nicht P0** — UFW hat keine IP-Regel für Port 8642, LAN `192.168.178.0/24` kann direkt zugreifen.

**Pitfalls beim Auth-Check:**
- `/health` ohne 401 ≠ kein Auth. `/health` ist oft by-design public. Der echte Test ist ein Daten-Endpoint (`/v1/models`, `/api/sessions`).
- `/health/detailed` vs `/health` — ersterer disclosed PID/Uptime/Version und sollte auth-protected sein. Wenn `/health/detailed` 401 gibt aber `/health` 200, ist Auth korrekt implementiert.
- `401 Invalid API key` ≠ `401 Unauthorized` — Ersteres beweist dass der Auth-Handler läuft und entscheidet. Zweiteres kann Middleware-Bypass sein.

**Empfehlung:** Bevor du einen World-Listener als P0 reportest, führe Phase 1-3 durch (Route Probing + Auth Verification + Config Source Tracing). In stabilen Hermes-Setups läuft Gateway bewusst auf `0.0.0.0` mit gültigem Bearer-Token — der echte Befund ist fehlendes Firewall-Fronting (= P1), nicht die Exposure selbst (= fälschlicherweise P0).

### Referenz-Dokument

Siehe `references/network-service-audit.md` — vollständiges Audit-Protokoll einer Gateway-Inspektion mit 6 Phasen, Route-Probe-Tabelle, Auth-Analyse, Network-Exposure-Matrix, Risk-Classification und Lessons Learned.

## Proaktives Session-Monitoring für Cloud-Coding-Agenten

**Wann triggern:** User fragt nach Sicherheitsvorkehrungen vor einer Session mit einem Cloud-Coding-Agenten (Grok 4.5, Claude Code, Codex CLI, Copilot CLI), möchte Netzwerkverkehr überwachen, bevor er einen Cloud-Agenten auf einem lokalen Repo startet, oder will ein reproduzierbares Sicherheits-Setup vor jeder Cloud-Agenten-Session.

**Ziel:** 4-stufiges Sicherheitssystem, das den Agenten nicht behindert, aber seine Aktivität transparent macht und Geheimnis-Exfiltration nachweisbar macht.

### Stufe 1: Pre-Flight-Hygiene (vor Session, ~30 Sek)

```bash
# 1. Secrets aus Working Tree isolieren
mv .env /run/secrets/project-$$.env
ln -s /run/secrets/project-$$.env .env

# 2. .gitignore-Audit — darf NICHTS mit Secret-Pattern getrackt haben
git ls-files | grep -iE '\.(env|key|pem|token|jwt|secret|credential)' && echo "🔴 STOPP"
```

**Pitfall:** `git ls-files` prüft was getrackt ist. Ein `.env` das nur existiert aber gitignored ist, ist kein Problem. Ein `.env` das getrackt ist, ist **P0 — nicht starten, erst `git rm --cached` + `.gitignore` fixen**.

**Pitfall 2:** Working-Dir-Sperre — Agent bekommt spezifisches Projektverzeichnis als CWD, nie Home oder Systemverzeichnis. Sonst hat der Agent über das Storage-API Zugriff auf alles.

### Stufe 2: Live-Monitoring (Sidecar während Session, 2. Terminal)

4 Kanäle parallel — alle Tools sind auf Bastis Host vorhanden:

| Kanal | Tool | Befehl | Erkenntnis |
|-------|------|--------|------------|
| Netzwerk | `tcpdump` | `tcpdump -i any -w /tmp/agent-session-$(date +%F).pcap 'not (host 127.0.0.1 or net 192.168.0.0/16)'` | Alle ausgehenden Verbindungen (SNI lesbar trotz TLS) |
| Verbindungen | `ss` | `watch -n1 'ss -tupn \| grep -E ":443\|:80"'` | Aktive HTTPS-Verbindungen mit PID |
| File-Deskriptoren | `lsof` | `sudo lsof -p $(pgrep -f "hermes\|grok\|claude-code\|codex") 2>/dev/null` | Welche Files der Agent geöffnet hat (Indiz auf `git cat-file`-Bypass) |
| Agentenlog | `tail -F ~/.hermes/logs/agent.log` | Gefiltert auf API-Endpoints (`grep -E "api\|grok\|xai\|x\.ai\|trace_upload\|tool_call"`) | Modellpfad und Provider-Routing live |

**Entscheidungsregel:** Stufe 2 immer machen. Tools sind auf dem Host vorhanden, keine Vorbereitungszeit, liefert nach Session-Ende einen pcap für die Retrospective.

### Stufe 3: Sandbox-Isolation (optional, nur für Wire-Capture-Studien)

**Nur sinnvoll wenn:**
- ✅ Konkrete Wire-Capture-Studie (beweisen wollen, was rausgeht)
- ✅ Echte Grok Build CLI Session (Risiko-Objekt aus dem Audit)
- ✅ Prod-Keys im selben Verzeichnis wie Agent
- ✅ Bugreport-Vorbereitung an Provider

**Overkill wenn:**
- ❌ Normale Coding-Session mit cleanem `.gitignore` + isoliertem Working Tree
- ❌ Kurzlebige Test-Keys (wöchentlich rotiert)
- ❌ Hermes/Nous-Routing (nicht Direkt-CLI)

**bwrap-Rezept (Bastis Host: `/usr/bin/bwrap` vorhanden):**
```bash
bwrap --unshare-net \
      --tmpfs /home \
      --bind ~/10-Projekte /home/bratan/10-Projekte \
      --ro-bind ~/.local/share ~/.local/share \
      --bind /tmp /tmp \
      --bind ~/.hermes ~/.hermes \
      --dev /dev --proc /proc -- \
      hermes
```

Hinweis: `--unshare-net` blockiert ALLE ausgehenden Verbindungen. Für eine Whitelist ist Network-Namespace + `nftables` nötig — deutlich aufwändiger, nur für längerfristige Setup-Läufe.

### Stufe 4: Post-Session-Audit

```bash
# 1. pcap sichern
mkdir -p ~/.hermes/wire-captures/
mv /tmp/agent-session-*.pcap ~/.hermes/wire-captures/

# 2. Host-Liste aus pcap extrahieren
tcpdump -nn -r ~/.hermes/wire-captures/agent-session-*.pcap \
  'tcp[tcpflags] & tcp-syn!=0 and not src net 127.0.0.0/8' | \
  awk '{print $5}' | sed 's/.[0-9]+$//' | sort -u
# Erwartbar: LLM-Provider, GitHub, PyPI/npm-Registry
# Unerwartbar: api.mixpanel.com, grok.com/_data, storage.googleapis.com → 🔴

# 3. .gitignore-Drift prüfen
cd /pfad/zum/projekt
git status --short | grep -iE '\.(env|key|pem|token)' && echo "🔴 Drift!"

# 4. Key-Rotation evaluieren
# Key im Chat/Agentenkontext gewesen? → P0 — Rotation freigeben
# Key nur in .env, nie im Chat? → 🟢 — keine Aktion
```

### 4b. Manual Connection Forensic Trace (Sidecar-Tot / Post-Facto)

> **Für Bulk-Capture-Analyse (voraufgezeichnete `ss`-Logs mit N Snapshots):**  
> Siehe `references/wire-capture-bulk-analysis.md` — dedizierte Methodik für  
> Multi-Snapshot-Parsing, Deduplizierung und Orphan-Analyse. Dies ergänzt die  
> Live-Forensik hier (Einzelsnapshot vs. zeitliche Verdichtung).

**Wann triggern:** Der Sidecar-Monitor (Stufe 2) wurde nicht gestartet, ist während
des Modellwechsels gestorben, oder der User will nachträglich alle Verbindungen
eines abgeschlossenen Modellwechsels verifizieren.

**Prinzip:** Statt pcap-Aufzeichnung wird der **aktuelle** Verbindungszustand
genommen und mit Prozess-Info, Geolocation, DNS und Config cross-referenziert.

#### Schritt 1: Sidecar alive?

```bash
set -euo pipefail
ps -eo pid,etime,cmd | grep -E 'grok-monitor|session-trace' | grep -v grep
ls -la /tmp/grok-monitor-state/ 2>/dev/null
find /tmp ~/.hermes -maxdepth 6 -name '*<session-id>*' 2>/dev/null
```

**Ist der Sidecar tot:** Weiter mit Schritt 2. **Lebt er noch:** `process(action='poll')`
für aktuellen Stand, dann pcap aus Stufe 4a extrahieren.

#### Schritt 2: Aktive Verbindungen erfassen

```bash
set -euo pipefail
# Alle aktuellen TCP-Verbindungen mit PID
ss -tupn

# Nur externe (nicht-RFC1918) Verbindungen
ss -tn state established | awk 'NR>1 && $5!~/^127\./ && $5!~/^10\./ &&
  $5!~/^192\.168\./ && $5!~/^172\.(1[6-9]|2[0-9]|3[01])\./ && $5!~/^::1$/ {print}'
```

**Pitfall:** `ss` ohne `sudo` zeigt nicht immer den Process-Owner.
Fehlende PID ist meist Firefox/Chrome/Electron-Helper (Kernel-Permissions-Limit
`CONFIG_NET_NS`). Kein Sicherheitsproblem — Ziel-IP reicht für Bewertung.

#### Schritt 3: Prozess-Identität pro Verbindung

```bash
set -euo pipefail
for pid in $(ss -tupn 2>/dev/null | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u); do
  [ -d /proc/$pid ] || continue
  comm=$(cat /proc/$pid/comm 2>/dev/null)
  cmd=$(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null | head -c 120)
  printf 'pid=%s comm=%s cmd=%s\n' "$pid" "$comm" "$cmd"
done
```

**Pitfall:** `hermes-cli` (Python-Gateway) ist kein Cloud-Agent — es ist der
Hermes-Gateway-Service. Dessen API-Calls zum konfigurierten Provider sind erwartbar.

#### Schritt 4: Geolocation pro Peer-IP

```bash
set -euo pipefail
for ip in <peer-ip1> <peer-ip2>; do
  echo "--- $ip ---"
  curl -s -m 8 "https://ipinfo.io/$ip/json"
  echo
done
```

**Auswertung:**

| Feld | Bedeutung |
|------|-----------|
| `org` | AS + Owner (z.B. `AS45102 Alibaba (US) Technology`) |
| `country` | Rechtsraum (US = CLOUD Act, DE = DSGVO) |
| `anycast` | true = Cloud-Edge-Node, kein Dedicated-Server |
| `hostname` | Reverse-DNS (z.B. `static.137...your-server.de` = Hetzner) |

#### Schritt 5: DNS-Cross-Reference (die Schlüssel-Validierung)

```python
import socket
hosts = ['api.minimax.io', 'api.openai.com', 'api.anthropic.com',
         'api.x.ai', 'api.nousresearch.com', 'api.telegram.org']
for host in hosts:
    ips = sorted({r[4][0] for r in socket.getaddrinfo(host, 443, type=1)})
    print(f'{host} -> {ips}')
    if '<verdaechtige-ip>' in ips:
        print('  ** MATCH — legitimiert **')
```

**Regel:** Wenn die verdächtige IP in der DNS-Response eines bekannten
API-Endpoints auftaucht → **kein Finding**. Der Traffic geht zu einem
Anycast-Edge des Providers.

#### Schritt 6: Config-Cross-Reference

```bash
set -euo pipefail
grep -nE 'provider:|base_url:' ~/.hermes/config.yaml | grep -vE '#|^\s*$' | head -30
```

#### Schritt 7: Report-Struktur

```
## Connection Audit — YYYY-MM-DDTHH:MM:SS

### Sidecar Status
- War aktiv von [start] bis [ende/vermutet tot]

### Aktive Verbindungen (N = x)
| Peer | AS / Owner | PID → Process | Verdict |
|---|---|---|---|
| 47.89.x.x:443 | Alibaba US / AS45102 | hermes-cli | ✅ MiniMax-API (DNS verifiziert) |
| ... | ... | ... | ✅/⚠️/🔴 |

### Unklassifiziert (⚠️)
Peer-IPs ohne klaren Owner und ohne bekannten Dienst.

### Fazit
- [N] Verbindungen geprüft
- [N] ✅ erwartbar (MiniMax, Valve, Flathub, Anthropic, ...)
- [N] ⚠️ unklassifiziert
- 🔴/🟢 Gesamtbewertung
```

**Pitfall:** ⚠️-Verbindungen sind kein Grund für Panik. Auf einem Desktop
laufen 10–20 Hintergrunddienste ohne vollständige Transparenz (Browser-Tabs,
GNOME-Software, Snap-Updater, Flatpak-Updater). Nur peers mit **unbekanntem
Port, unbekanntem Owner UND ungewöhnlichem Traffic-Volumen** sind P0-würdig.

### Modellevaluierung (optional, nach Session)

Nach einer Session mit einem neuen Modell kann eine strukturierte Evaluierung
in 5 Dimensionen durchgeführt werden, basierend auf realen Session-Daten:

| Dimension | Skala | Datenquellen |
|-----------|-------|-------------|
| Coding-Kompetenz | 1-10 | Code-Qualität, autonom gelöste Aufgaben, Fehlerrate |
| Tool-Disziplin / Sicherheit | 1-10 | Bash-Hygiene, Secret-Handling, Klärungsverhalten |
| Kontext-Stabilität | 1-10 | Token-Konsistenz, Cache-Hit-Rate, Drift-Freiheit |
| Anbieter-Transparenz | 1-10 | Vendor-Statements, CVE-Track-Record, Postmortem-Kultur |
| Preis-Leistung | 1-10 | Token-Kosten, Cache-Effizienz, Gesamtkosten pro Task |

Für jedes Modell die Evaluierung als `references/<model>-assessment-<date>.md` ablegen.
Siehe auch: `references/grok45-model-assessment-detail.md` (Beispiel mit Session-Daten).

Die Evaluierung wird **nicht** in Mnemosyne oder Memory gespeichert — sie ist
eine Momentaufnahme, die bei der nächsten Modellversion bereits veraltet sein kann.
Stattdessen: Referenzdatei im Skill, die bei Bedarf aktualisiert wird.
