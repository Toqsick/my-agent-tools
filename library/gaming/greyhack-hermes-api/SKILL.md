---
name: greyhack-hermes-api
title: GreyHack + Hermes API Integration (Stufe 2 — v2 mit LLM)
description: "Use when user asks for Hermes↔GreyHack API integration, local HTTP API server on port 8333, LLM-driven GreyHack in-game chat. NOT for GreyHack scripting (use greyhack) or non-Hermes GreyHack bots. Hermes runs as local HTTP-API server (port 8333) for GreyHack."
tags:
- greyhack
- greyscript
- api
- integration
- gaming
- llm
version: 1.0.0
author: Hermes Agent
license: MIT
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['greyhack', 'hermes', 'local', 'http', 'server']
keywords: ['greyhack', 'hermes', 'local', 'http', 'server']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['github-grayhack-workflow', 'greyhack-game-observer', 'greyhack-smart-macro']
---


# GreyHack Hermes API Integration

## Stufen-Überblick

| Stufe | Name | Status | Beschreibung |
|-------|------|--------|--------------|
| 1 | CLI-Integration | ✅ | Python-Skripte greifen auf GreyHack DB zu |
| 2 | HTTP-API (v2) | ✅ | Hermes als lokaler Server (Port 8333) mit echter LLM-Anbindung via Nous Portal, Host-Terminal CLI, @reboot-Cron |
| 3 | In-Game Player | ⚠️ | Hermes-Computer in DB eingetragen (IP: 172.217.22.14), Daemon erstellt, aber Deployment ins Spiel erfordert manuelles Copy-Paste oder greybel-js (GreyScript hat kein HTTP) |

## Stufe 2 — HTTP-API v2 (mit LLM)

Die API ist NICHT für GreyScript-Zugriff gedacht (GreyScript hat kein `HTTP.Request()`).
Der praktische Workflow ist **Alt-Tab + Host-Terminal**:

1. Im Spiel: Frage notieren oder Problem identifizieren
2. Alt-Tab: `~/bin/hermes-ask "Frage"` eingeben
3. Echte KI-Antwort lesen
4. Alt-Tab zurück → Aktion ausführen

### Host-Terminal CLI (`~/bin/hermes-ask`)

```bash

set -euo pipefail
~/bin/hermes-ask status              # Server-Check (ob online)
~/bin/hermes-ask "Wie hacke ich SSH?" # Freitext-Frage ans LLM
~/bin/hermes-ask -g backdoor         # GreyScript-Code generieren
~/bin/hermes-ask -a 192.168.1.10 22,80  # Port-Liste analysieren
```

Flags:
- Kein Flag = `POST /ask` — Freitext-Frage via Nous Portal LLM
- `-g` = `POST /generate` — GreyScript-Code generieren (tool: portscan, backdoor, bruteforce, generic)
- `-a` = `POST /analyze` — Port-Liste analysieren + nächste Schritte

### Server (`~/bin/hermes-gh-api-server.py`)

**v2 Features:**
- Echte LLM-Antworten via Nous Portal (OpenAI-Client) mit Modell `deepseek/deepseek-v4-flash`
- Automatischer Token-Refresh (kein manuelles Re-Login)
- Hermes' venv Python (`~/.hermes/hermes-agent/venv/bin/python3`) — openai bereits installiert
- Logging nach `~/.hermes/logs/hermes-gh-api.log`

```bash

set -euo pipefail
# Manueller Start
~/.hermes/hermes-agent/venv/bin/python3 ~/bin/hermes-gh-api-server.py &

# Status-Check
curl http://127.0.0.1:8333/status
```

Endpunkte (ALLE mit echten LLM-Antworten, nicht nur Templates):
- `GET /status` — Server online + Modell-Info
- `POST /ask` — Freitext-Frage an DeepSeek V4 Flash
- `POST /analyze` — Port-Liste analysieren → nächste Schritte (mit LLM-Kontext)
- `POST /generate` — GreyScript-Code generieren (tool: portscan, backdoor, bruteforce, generic)
- `POST /crack` — Passwort-Cracking-Tips (mit LLM-Strategie)

Autostart (crontab):
```

set -euo pipefail
@reboot sleep 10 && /home/bratan/.hermes/hermes-agent/venv/bin/python3 /home/bratan/bin/hermes-gh-api-server.py > ~/.hermes/logs/hermes-gh-api-cron.log 2>&1
```

### GreyScript-Client (`~/greyhack-tools/hermes_api.src`)

**⚠️ NICHT KOMPILIERBAR IN VANILLA GREYSCRIPT.** Der Client verwendet `HTTP.Request()`, das in GreyScript NICHT existiert. Die `.src`-Datei liegt nur als Blueprint/Referenz im Repo — nicht in `master_installer.src` aufnehmen.

Im Spiel (nur wenn HTTP verfügbar wäre, z.B. via BepInEx):
```

set -euo pipefail
hermes_api status
hermes_api generate {"tool": "portscan"}
hermes_api analyze {"target": "10.0.0.5", "ports": "22,80"}
```

**Praktischer Workflow stattdessen:** Alt-Tab + `~/bin/hermes-ask "frage"`

### Launcher-Integration

*Entfernt (v2) — `hermes_api.src` wurde aus dem Installer entfernt, weil GreyScript kein HTTP hat.
Der Hermes-Zugriff läuft ausschließlich über Host-Terminal (`~/bin/hermes-ask`), nicht übers Spiel.*

Falls später ein BepInEx-Plugin HTTP ermöglicht, kann `hermes_api.src` wieder in den Launcher (Tool 11) aufgenommen werden.

## Stufe 3 — Hermes als In-Game-Computer

Hermes existiert als eigener Computer im GreyHack-Netzwerk mit eigener IP, Hardware und Filesystem.

### DB-Einträge (einmalig setzen)

```python
import sqlite3, json

DB = "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1. Hermes-Computer
computer_id = "329730062"  # oder hash(hermes_ip)
hermes_ip = "172.217.22.14"

filesystem = {"computerID": computer_id, "nombre": "/", "files": [], "folders": [...]}

cur.execute("""
    INSERT OR REPLACE INTO Computer (ID, FileSystem, IsPlayer, Users)
    VALUES (?, ?, 0, ?)
""", (computer_id, json.dumps(filesystem), json.dumps({
    "root": {"password": "rootpass", "home": "/root"},
    "hermes": {"password": "hermespass", "home": "/home/hermes"}
})))

# 2. Netzwerk-Verbindung
player_router = "158.190.150.57:1259451457"
cur.execute("""
    INSERT OR REPLACE INTO PlayerConns (ID, ComputerID, RouterID, LocalIp, PublicIp)
    VALUES (?, ?, ?, '192.168.1.22', ?)
""", (f"conn_{computer_id}", computer_id, player_router, hermes_ip))

conn.commit()
```

set -euo pipefail
### Hermes-Daemon (`~/greyhack-tools/hermes_daemon.src`)

Autonomer Prozess im Spiel:
- Startet mit `hermes_daemon --background`
- Pingt API alle 60 Sekunden (`/status`)
- Schreibt Log nach `/home/Bratan/.logs/hermes_daemon.log`
- Reagiert auf API-Befehle (zukünftig: Portscans, Exploits)

```
hermes_daemon status   # Status prüfen
hermes_daemon stop     # Beenden
hermes_daemon --help   # Hilfe
```

set -euo pipefail
**Wichtig:** Daemon als `bin` File markieren (`isBinario: true` in DB) damit `shell.launch()` es ausführen kann.

### SSH-Zugriff auf Hermes-Computer

```
ssh hermes@172.217.22.14
# Passwort: hermespass
```

Nach erfolgreichem Login: Hermes-Computer hat eigenes `get_shell` + `host_computer`.

## Deployment (Stufe 2→3)

Siehe `greyhack-greyscript` Skill, Abschnitt "Deployment". Zusammenfassung:
- Steam-Flatpak → kein Host-Dateizugriff
- GreyScript hat KEIN HTTP → kein direkter Download möglich
- Lösung: greybel-js Installer oder manuelles Copy-Paste
- ODER: Direkte SQLite-Injektion in `GreyHackDB.db`

## Wichtige Pfade

| Pfad | Funktion |
|------|----------|
| `~/bin/hermes-gh-api-server.py` | API-Server v2 mit LLM (Stufe 2) |
| `~/bin/hermes-ask` | Host-Terminal-CLI (Flags: -g generate, -a analyze) |
| `~/greyhack-tools/hermes_api.src` | GreyScript-Client (⚠️ nicht kompilierbar, Blueprint only) |
| `~/greyhack-tools/hermes_daemon.src` | In-Game-Daemon (Stufe 3, Blueprint) |
| `~/.hermes/logs/hermes-gh-api.log` | Server-Log |
| `~/.hermes/logs/hermes-gh-api-cron.log` | Cron-Start-Log |
| `/mnt/DATA/.../Grey Hack_Data/GreyHackDB.db` | Spiel-DB (Stufe 3) |

## Fehlerbehandlung

| Fehler | Ursache | Fix |
|--------|---------|-----|
| `[X] Server offline` | API-Server nicht gestartet | `killall python3; ~/.hermes/hermes-agent/venv/bin/python3 ~/bin/hermes-gh-api-server.py &` |
| `[X] Connection refused` | Port 8333 blockiert | `ss -tlnp \| grep 8333` prüfen; Server neustarten |
| `[!] Token expired` | Nous Auth-Token abgelaufen | Server hat Auto-Refresh — sollte selbst heilen. Prüfen: `curl localhost:8333/status` — wenn Modell null ist, Token manuell erneuern: `hermes login --no-browser` |
| `[!] 401 / credential pool` | Hilfs-Provider fehlt | `hermes config set auxiliary.vision.provider nous && hermes config set auxiliary.compression.provider nous && hermes config set auxiliary.web_extract.provider nous && hermes gateway restart` |
| `[X] Keine Antwort` | LLM-Timeout oder API-Error | `~/.hermes/logs/hermes-gh-api.log` prüfen; Netz verbunden? |
| `command not found` nach Neustart | Binaries im RAM | Installer neu ausführen oder `.src` in DB persistieren |
| `Computer not found` | Stufe 3 DB-Eintrag fehlt | SQLite-Eintrag in `Computer`-Tabelle prüfen |
| `SSH timeout` | Netzwerk-Verbindung fehlt | `PlayerConns`-Eintrag prüfen |

## Nächste Schritte (offen)

- Daemon: Autonome Scans + Exploit-Workflows
- Bidirektionale Kommunikation: API → Daemon → Spiel-Aktionen
- Hermes als vertrauenswürdiger Relay im Netzwerk

## Support Files

- `references/stage3-deployment-notes.md` — Session-Notizen vom 06.06.2026: was funktioniert, was blockiert, getestete Ansätze

## 🧭 Related Skills (Cross-Cluster Navigation)

Skills that support this GreyHack-Hermes-API integration but live elsewhere:

- **`skill-navigator`** (orchestration/) — Meta-Navigator for all 169 Hermes skills. Load FIRST when deciding which skill applies.
- **`multi-agent-pitfalls-cheatsheet`** (orchestration/) — TRIGGER-WATCHLIST for `delegate_task` calls. Load BEFORE spawning subagents for GreyHack-API investigations. Pitfall #28 (`model` param silently ignored) and Pitfall #29 (subagent summary ≠ file) are especially relevant for in-game API integrations.
- **`multi-agent-orchestration`** (orchestration/) — The 3-Expert Research PATTERN. Useful for the planned in-game Hermes co-pilot investigations (API server, Bridge, Steam-Overlay Web-UI).

**GreyHack-Hermes-API → Orchestration Workflow:** When integrating in-game Hermes with the API server, load cheatsheet + orchestration together. The cheatsheet's Pitfall #31 (Background-Review timeouts) is particularly relevant for the bridge/CORS code patterns.
